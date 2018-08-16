#!/usr/bin/env python2

# This python module takes care of getting required details
# and sending email to user about build status

import base64
import json
import ssl
import urllib2

from ccp.lib.command import run_cmd


def get_url(url):
    """
    Perform GET call on given URL
    """
    username = "navid-admin"
    token = "6ec99caeeb9407feb7305e1136816c70"

    auth_header = base64.b64encode('%s:%s' % (username, token))

    r = urllib2.Request(url)

    r.add_header("Authorization", "Basic %s" % auth_header)

    return urllib2.urlopen(r, context=ssl._create_unverified_context())


def get_cause_of_build(namespace, jenkins_url, job, build_number):
    """
    Figure out cause of the build trigger
    """

    url = ("https://{jenkins_url}/job/{namespace}/job/{namespace}-{job}/"
           "{build_number}/api/json").format(
               jenkins_url=jenkins_url,
               namespace=namespace,
               job=job,
               build_number=build_number)

    print ("Opening URL {}".format(url))
    try:
        response = get_url(url)
        response = json.loads(response.read())
    except Exception as e:
        print ("Error opening URL {}".format(e))
        return "Error fetching cause of build"

    try:
        cause = response["actions"][0]["causes"][0]["shortDescription"]

        if cause == "Started by an SCM change":
            return "Git commit {}".format(
                response["actions"][2]["lastBuiltRevision"]["SHA1"]
            )
        elif "Started by upstream project" in cause:
            return "Change in upstream project {}".format(
                response["actions"][0]["causes"][0]["shortDescription"].split(
                    '"')[1]
            )
        elif "Started from command line" in cause:
            return "RPM update in enabled repos"
        elif "Started by user" in cause:
            return "Manually triggered by admin"
        else:
            return str(cause)
    except KeyError as e:
        print ("Invalid JSON response from Jenkins. {}".format(e))
        return "Unable to find cause of build"


def send_email(cause_of_build):
    subject = "SUCCESS: Container build is complete."

    body = """\
Container build is complete.
Cause of build:\t{}""".format(cause_of_build)

    command = ("echo -e '{body}'| mail -r nshaikh@redhat.com -S smtp=smtp://mail.centos.org "
               "-s '{subject}' shaikhnavid14@gmail.com")

    command = command.format(
        body=escape_text(body),
        subject=subject)
    run_cmd(command, shell=True)


def escape_text(text):
    return text.replace("\n", "\\n").replace("\t", "\\t")


def notify(namespace, jenkins_url, job, build_number):

    cause_of_build = get_cause_of_build(namespace, jenkins_url, job, build_number)
    send_email(cause_of_build)


if __name__ == "__main__":
    import sys
    namespace = sys.argv[1].strip()
    jenkins_url = sys.argv[2].strip()
    job = sys.argv[3].strip()
    build_number = sys.argv[4].strip()

    notify(namespace, jenkins_url, job, build_number)
