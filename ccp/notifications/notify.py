#!/usr/bin/env python2

# This python module takes care of getting required details
# and sending email to user about build status


import sys

from ccp.lib.openshift import BuildInfo
from ccp.lib.email import SendEmail


class Notify(object):
    """
    Notify class has related methods to notify
    user about build status and details
    """

    def __init__(self):
        self.buildinfo_obj = BuildInfo(
            service_account="sa/jenkins",
            required_fields=[
                "NOTIFY_EMAIL",
                "DESIRED_TAG",
                "REGISTRY_URL",
                "FROM_ADDRESS",
                "SMTP_SERVER",
                # this will be derived in BuildInfo
                "CAUSE_OF_BUILD"])
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
        cause: Cause of the build
        """
        status = "Success" if status else "Failure"
        success_template = """\
{0: <20} {1}
{2: <20} {3}
{4: <20} {5}"""

        failure_template = """\
{0: <20} {1}
{2: <20} {3}"""

        footer = """\
--
Do you have a query?
Talk to Pipeline team on #centos-devel at freenode
CentOS Community Container Pipeline Service
https://wiki.centos.org/ContainerPipeline
https://github.com/centos/container-index
"""

        if status:
            body = success_template.format(
                "Build Status:", status,
                "Repository:", repository,
                "Cause of build:", cause)
        else:
            body = failure_template.format(
                "Build Status:", status,
                "Cause of build:", cause)

        body = body + "\n" + footer

        return body

    def notify(self,
               status, namespace, jenkins_url,
               image_name, build_number):
        """
        Get notifications details and sends email to user
        """
        build_info = self.buildinfo_obj.get_build_info(
            namespace, jenkins_url,
            image_name, build_number)

        # convert status to boolean
        # possible values are ["success", "failed"]
        status = True if status == "success" else False

        # get the repository name (without tag)
        repository = "https://" + build_info.get("REGISTRY_URL") + \
            "/" + image_name.split(":")[0]

        cause = build_info.get("CAUSE_OF_BUILD")

        # subject should have image_name without registry
        subject = self.subject_of_email(status, image_name)

        # body should have repository name (without tag)
        body = self.body_of_email(status, repository, cause)

        print ("Sending email to {}".format(build_info.get("NOTIFY_EMAIL")))

        self.sendemail_obj.email(
            build_info.get("SMTP_SERVER"),
            subject, body,
            build_info.get("FROM_ADDRESS"),
            [build_info.get("NOTIFY_EMAIL")])


if __name__ == "__main__":
    status = sys.argv[1].strip()
    namespace = sys.argv[2].strip()
    jenkins_url = sys.argv[3].strip()
    image_name = sys.argv[4].strip()
    build_number = sys.argv[5].strip()

    notify_object = Notify()
    notify_object.notify(
        status, namespace, jenkins_url,
        image_name, build_number)
