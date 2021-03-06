#!/usr/bin/env python

# OpenShift operations related utilities

import json
import ssl
import sys
import urllib2

from ccp.lib.utils.command import run_command
from ccp.lib.clients.openshift.client import OpenShiftCmdClient
from ccp.lib.utils.retry import retry


class BuildInfo(object):
    """
    Class having utilities for fetching the Jenkins build info
    """

    def __init__(self, service_account="sa/jenkins", required_fields=[]):
        """
        Initialize the object by specifying the service_account for
        Jenkins and specifying the required_fields expected while
        retrieving build information.
        """
        self.service_account = service_account
        # given the list of fields,
        self.required_fields = required_fields

    def get_url(self, url, token, context=None):
        """
        Opens the given URL using the given token for authorization
        and using given context if any and
        returns the response received from opening URL.
        """
        # create request object
        r = urllib2.Request(url)

        # add authorization header
        r.add_header("Authorization",
                     "Bearer %s" % token.strip())

        # if context is not given, create one
        if not context:
            context = ssl._create_unverified_context()

        return urllib2.urlopen(r, context=context)

    def parse_cause_of_build(self, response):
        """
        Parse the JSON response containing jenkins job details
        """
        cause_of_build = None
        try:

            if response["number"] == 1:
                return "First build of the container image"

            for _class in response["actions"]:
                if "_class" not in _class:
                    continue
                # this class refers to cause of build / causeAction
                # which contains all the possible values for cause of build
                if _class["_class"] == "hudson.model.CauseAction":
                    for cause in _class["causes"]:
                        # refers to SCM trigger
                        if cause["_class"] == \
                                "hudson.triggers.SCMTrigger$SCMTriggerCause":
                            cause_of_build = cause["shortDescription"]
                            break
                        # refers to parent child relationship / depends-on
                        elif cause["_class"] == \
                                "hudson.model.Cause$UpstreamCause":
                            # process upstream project name
                            # eg: cccp/cccp-test-anomaly-latest
                            ups_proj = cause["upstreamProject"].split(
                                "/")[-1].split("-")
                            # form appid/jobid:desiredtag
                            ups_proj = "/".join(
                                ups_proj[1:-1]) + ":" + ups_proj[-1]

                            cause_of_build = ("Parent container image "
                                              "{} is rebuilt".format(ups_proj))
                            break
                # jenkins manual trigger is not available
                # all the builds are intitiated from openshift
                # shortDescription in this case is like
                # OpenShift Build cccp/test-python-release-5 from $GITURL
                # that's a manual trigger
                        else:
                            cause_of_build = ("Update to build configurations "
                                              "of the container image")

                    # fail over / if _class is not the one expected
                    if not cause_of_build:

                        # there are two _class available
                        # io.fabric8.jenkins.openshiftsync.BuildCause
                        # hudson.triggers.SCMTrigger$SCMTriggerCause

                        # grab the one available
                        cause_of_build = \
                            _class["causes"][0]["shortDescription"]
                        break

            # this is to find the git commit in subsequent section of response
            if cause_of_build == "Started by an SCM change":
                for _class in response["actions"]:
                    if "_class" not in _class:
                        continue
                    # this class has build data details
                    if _class["_class"] == "hudson.plugins.git.util.BuildData":
                        cause_of_build = \
                            "Git commit {} to branch {} of repo {}."
                        return cause_of_build.format(
                            # referencing 0 here as 1 jenkins job yield 1 build
                            _class["lastBuiltRevision"]["branch"][0]["SHA1"],
                            _class["lastBuiltRevision"]["branch"][0]["name"],
                            _class["remoteUrls"][0])

            if not cause_of_build:
                return "Unable to find the cause of build."
            return cause_of_build

            # TODO: Other cases of cause to be worked upon
            # elif "Started from command line" in cause:
            #     return "RPM update in enabled repos"

        except KeyError as e:
            print ("Invalid JSON response from Jenkins. {}".format(e))
            return "Unable to find the cause of build."

    def parse_jenkins_job(self, response):
        """
        Parse Jenkins job details and grab the needed details
        """
        build_info = {}
        try:
            # build result/status possible values = SUCCESS/FAILURE
            build_info["RESULT"] = response.get("result")

            # now parsing other details
            actions = response.get("actions")
            # actions contains a list of dictionaries

            for each in actions:
                # here each might be empty dict too
                if not each.get("_class"):
                    continue

                if each.get("_class") == "hudson.model.ParametersAction":
                    # parameters is a list of dict
                    for param in each.get("parameters"):
                        build_info[param["name"]] = param["value"]
        except KeyError as e:
            print ("Error parsing build details.")
            raise(e)

        build_info["CAUSE_OF_BUILD"] = self.parse_cause_of_build(response)

        # check if required_fields are in build_info
        if not set(self.required_fields).issubset(build_info.keys()):
            print ("Could not retrieve required field(s) from build details.")
            print ("Missing field(s) {}".format(
                list(set(self.required_fields).difference(build_info.keys()))))
            sys.exit(1)

        return build_info

    def get_build_info(
            self, namespace, jenkins_url, pipeline_name, build_number):
        """
        Given build identifiers, use Jenkins REST APIs to figure
        out details of the build
        """
        url = ("https://{jenkins_url}/job/{namespace}/job/"
               "{namespace}-{pipeline_name}/{build_number}/api/json".format(
                   jenkins_url=jenkins_url,
                   namespace=namespace,
                   pipeline_name=pipeline_name,
                   build_number=str(build_number)))

        print ("Opening URL to details of the build\n{}".format(url))

        try:
            c = OpenShiftCmdClient()
            token = c.get_sa_token_from_openshift(
                namespace,
                sa=self.service_account
            )
            response = self.get_url(url, token)
            response = json.loads(response.read())
        except Exception as e:
            print ("Error opening URL {}".format(e))
            raise(e)
        else:
            return self.parse_jenkins_job(response)
