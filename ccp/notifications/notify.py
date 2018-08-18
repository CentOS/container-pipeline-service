#!/usr/bin/env python2

# This python module takes care of getting required details
# and sending email to user about build status


import json
import ssl
import sys
import urllib2

from ccp.lib.command import run_cmd


class BuildInfo(object):
    """
    Given the build identifiers, fetch the build details
    """

    def __init__(self, service_account="sa/jenkins"):
        self.service_account = service_account

    def get_url(self, url, token, context=None):
        """
        Gets the given URL and uses given token for authorization
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

    def get_token(self):
        """
        For given service account, get the token using oc secrets
        """
        command = """\
oc get {0} --template='{{range .secrets}}{{ .name }} {{end}}' |
xargs -n 1 oc get secret --template='{{ if .data.token }}{{ .data.token }}\
{{end}}' | head -n 1 | base64 -d - """.format(
            self.service_account)
        # run the oc command
        token = run_cmd(command, shell=True)
        # strip any extra characters while reading stdout
        return token.strip()

    def get_jenkins_pipeline_job_name(self, namespace, image_name):
        """
        Returns the jenkins pipeline job name.
        Its formatted at namespace-appid-jobid-desiredtag.
        """
        pipeline = image_name.replace("/", "-").replace("_", "-").replace(
            ":", "-")
        return "{}-{}".format(namespace, pipeline)

    def parse_jenkins_job_details(self, response):
        """
        Parse the JSON response containing jenkins job details
        """
        try:
            cause_of_build = None
            for _class in response["actions"]:
                if "_class" not in _class:
                    continue
                # this class refers to cause of build / causeAction
                if _class["_class"] == "hudson.model.CauseAction":
                    for cause in _class["causes"]:
                        # refers to SCM trigger
                        if cause["_class"] == \
                                "hudson.triggers.SCMTrigger$SCMTriggerCause":
                            cause_of_build = cause["shortDescription"]
                            break
                    # fail over / if _class is not the one expected
                    if not cause_of_build:

                        # there are two _class available
                        # io.fabric8.jenkins.openshiftsync.BuildCause
                        # hudson.triggers.SCMTrigger$SCMTriggerCause

                        # grab the one available
                        cause_of_build = \
                            _class["causes"][0]["shortDescription"]
                        break

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
                return "Unable to find cause of build."
            return cause_of_build

            # TODO: Other cases of cause to be worked upon
            # "Started by upstream project"
            #     return "Change in upstream project {}".format(
            #         response["actions"][0]["causes"][0]["shortDescription"].split(
            #             '"')[1]
            #     )
            # elif "Started from command line" in cause:
            #     return "RPM update in enabled repos"
            # elif "Started by user" in cause:
            #     return "Manually triggered by admin"
        except KeyError as e:
            print ("Invalid JSON response from Jenkins. {}".format(e))
            return "Unable to find cause of build."

    def get_cause_of_build(self,
                           namespace, jenkins_url, image_name, build_number):
        """
        Given build identifies, use Jenkins REST APIs to figure
        out cause of build
        """
        # populate the jenkins pipeline job name
        job = self.get_jenkins_pipeline_job_name(
            namespace, image_name)

        url = ("https://{jenkins_url}/job/{namespace}/job/"
               "{job}/{build_number}/api/json".format(
                   jenkins_url=jenkins_url,
                   namespace=namespace,
                   job=job,
                   build_number=build_number))

        print ("Opening URL to get cause of build\n{}".format(url))

        try:
            token = self.get_token()
            response = self.get_url(url, token)
            response = json.loads(response.read())
        except Exception as e:
            print ("Error opening URL {}".format(e))
            return "Error fetching cause of build."

        else:
            return self.parse_jenkins_job_details(response)


class SendEmail(object):
    """
    This class has related methods for sending email
    """

    def escape_text(self, text):
        """
        Given text, escapes newlines and tabs
        """
        return text.replace("\n", "\\n").replace("\t", "\\t")

    def email(self,
              smtp_server, sub, body,
              from_add, to_adds, cc_adds=[]):
        """
        Send email using given details
        smtp_server: URL of smtp server
        sub: Subject of email
        body: Body of email
        from_add: From address
        to_adds: A list of to addresses
        cc_adds: (optional) A list addresses to mark in Cc
        """
        command = """\
echo -e '{body}' | mail -r {from_address} {cc_opts} -S \
smtp={smtp_server} -s "{subject}" {to_addresses}"""

        # it would return '' for [] / no cc_add
        cc_opts = " ".join(map("-c {0}".format(cc_adds)))

        # to addresses
        to_addresses = " ".join(to_adds)

        # escape the \n and \t characters
        body = self.escape_text(body)

        command.format(
            body=body,
            from_address=from_add,
            cc_opts=cc_opts,
            smtp_server=smtp_server,
            subject=sub,
            to_addresses=to_addresses)

        # send email
        run_cmd(command, shell=True)
        print ("Email sent to {}".format(to_adds))


class Notify(object):
    """
    Notify class has related methods to notify
    user about build status and details
    """

    def __init__(self):
        self.buildinfo_obj = BuildInfo()
        self.sendemail_obj = SendEmail()

    def subject_of_email(self, status, build):
        """
        Returns subject of email
        status: Status of build - True=Success False=Failure
        project: Name of the project/build
        """
        s_sub = "SUCCESS: Container build {} is complete"
        f_sub = "FAILED: Container build {} has failed"

        if status:
            return s_sub.format(build)
        else:
            return f_sub.format(build)

    def body_of_email(self, status, repository, cause):
        """
        Generate the body of email using given details
        status: Status of build - True=Success False=Failure
        image: Image name
        cuase: Cause of the build
        """
        status = "Success" if status else "Failure"
        template = """\
{0: <20} {1}
{2: <20} {3}
{4: <20} {4}"""

        footer = """\
--
Do you have a query ?
Talk to Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline"""

        body = template.format(
            "Build Status:", status,
            "Repository:", repository,
            "Cause of build:", cause)

        body = body + "\n\n" + footer

        return body

    def notify(self,
               namespace, status, jenkins_url,
               image_name, image_name_with_registry,
               build_number, smtp_server, from_address,
               notify_email):
        """
        Get notifications details and sends email to user
        """
        status = True if status == "success" else False

        # get the repository name (without tag)
        # covers the cases of r.c.o/a/b:latest and a.b.c:5000/a/b:latest
        index = image_name_with_registry.rfind(":")
        if index != -1:
            repository = image_name_with_registry[:index]
        else:
            repository = image_name_with_registry

        cause = self.buildinfo_obj.get_cause_of_build(
            namespace, jenkins_url, image_name, build_number)

        # subject should have image_name without registry
        subject = self.subject_of_email(status, image_name)

        # body should have repository name (without tag)
        body = self.body_of_email(status, repository, cause)

        self.sendemail_obj.email(
            smtp_server,
            subject, body, from_address, [notify_email])


if __name__ == "__main__":
    namespace = sys.argv[1].strip()
    status = sys.argv[2].strip()
    jenkins_url = sys.argv[3].strip()
    image_name = sys.argv[4].strip()
    image_name_with_registry = sys.argv[5].strip()
    build_number = sys.argv[6].strip()
    smtp_server = sys.argv[7].strip()
    from_address = sys.argv[8].strip()
    notify_email = sys.argv[9].strip()

    notify_object = Notify()
    notify_object.notify(
        namespace, status, jenkins_url,
        image_name, image_name_with_registry,
        build_number, smtp_server, from_address,
        notify_email)
