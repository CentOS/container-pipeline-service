#!/usr/bin/env python2

# This python module takes care of getting required details
# and sending email to user about build status


import sys

from ccp.notifications.base import BaseNotify
from ccp.lib.openshift import BuildInfo
from ccp.lib.email import SendEmail


class BuildNotify(BaseNotify):
    """
    Notify class has related methods to notify
    user about build status and details
    """

    def __init__(self):
        # instantiate the base class
        super(BuildNotify, self).__init__()
        # create the buildInfo class object
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
        # create the SendEmail utility class object
        self.sendemail_obj = SendEmail()

    def subject_of_email(self, status, build):
        """
        Given the status and build/image name, returns the subject of email

        :param status: Status of container image build
        :type status bool
        :param build: Container image name without registry
        :param type str
        :return: Subject line of notification email in text
        """
        if status:
            return self.build_success_subj.format(build)
        else:
            return self.build_failure_subj.format(build)

    def body_of_email(self, status, repository, cause):
        """
        Generate the body of email using given details
        :param status: Status of container image build
        :type status bool
        :param repository: Repository name of image along with registry name
        :type repository str
        :param cause: Cause of the the build
        :type cause str
        :return: Email body of notification email in text
        """
        if status:
            body = self.build_success_body.format(
                "Build Status:", "Success",
                "Repository:", repository,
                "Cause of build:", cause)
        else:
            body = self.build_failure_body.format(
                "Build Status:", "Failure",
                "Cause of build:", cause)

        body = body + "\n\n" + self.email_footer

        return body

    def notify(self,
               status, namespace, jenkins_url,
               image_name, build_number):
        """
        Get notifications info and sends email to user

        :param status: Status of build in text ["success", "failure"]
        :type status bool
        :param namespace: Namespace in which build ran
        :type namespace str
        :param jenkins_url: Jenkins URL where build executed
        :type jenkins_url str
        :param image_name: Container image name without registry
        :type image_name str
        :param build_number: Container image build number
        :type build_number str / int
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

    notify_object = BuildNotify()
    notify_object.notify(
        status, namespace, jenkins_url,
        image_name, build_number)
