#!/usr/bin/env python2

# This python module takes care of getting required details
# and sending email to user about weekly scan


import sys

from ccp.notifications.base import BaseNotify
from ccp.lib.openshift import BuildInfo
from ccp.lib.email import SendEmail


class WeeklyScanNotify(BaseNotify):
    """
    WeeklyScanNotify class has related methods to notify
    user about weekly scan status and info
    """

    def __init__(self):
        # instantiate the base class
        super(WeeklyScanNotify, self).__init__()

        # create build info object to retrieve build info to send email
        self.buildinfo_obj = BuildInfo(
            service_account="sa/jenkins",
            required_fields=[
                "NOTIFY_EMAIL",
                "NOTIFY_CC_EMAILS",
                "REGISTRY_ALIAS",
                "REGISTRY_URL",
                "FROM_ADDRESS",
                "SMTP_SERVER"])
        # create send email utility object for sending emails
        self.sendemail_obj = SendEmail()

    def body_of_email(self, status, image_name, registry_url, registry_alias):
        """
        Generate the body of email for weekly scan notification email

        :param status: Status of build - True=Success False=Failure
        :type status bool
        :param image_name: Name of the image
        :type image_name str
        :param registry_url: Configured registry URL
        :type registry_url str
        :param registry_alias: Registry alias to be used in repository name,
            if it's value is "null", the $registry_url is used instead
        :type registry_alias str
        :return: Body of email in text
        """
        if registry_alias == "null":
            # get the repository name (without tag)
            repository = "https://" + registry_url + \
                "/" + image_name.split(":")[0]
        else:
            # if registry_alias is not "null", use it
            repository = "https://" + registry_alias + \
                "/" + image_name.split(":")[0]

        if status:
            body = self.weekly_body.format(
                "Scan status:", "Success",
                "Repository:", repository)
        else:
            body = self.weekly_body.format(
                "Scan status:", "Failure",
                "Repository:", repository)

        return body + "\n\n" + self.email_footer

    def image_absent_email_body(self):
        """
        Generates the body of email for weekly scan notification when
        image is absent in the registry and scan has failed.

        :return: Body of email in text
        """
        body = self.weekly_image_absent_body.format(
            "Scan status:",
            "Image is absent in the registry, scan is aborted.")
        return body + "\n\n" + self.email_footer

    def notify(self,
               status, namespace, jenkins_url,
               image_name, build_number, pipeline_name):
        """
        Notify the user by sending email about weekly scan info

        :param status: Status of weekly scan performed
                       ["success", "failed", "image_absent"]
        :type status str
        :param namespace: Namespace of the build
        :type namespace str
        :param jenkins_url: Jenkins URL to fetch the build info
        :type jenkins_url str
        :param image_name: Name of the scanned image
        :type image_name str
        :param build_number: Build number of weekly scan at Jenkins
        :type build_number str / int
        :param pipeline_name: Pipeline name
        :type pipeline_name str
        """

        build_info = self.buildinfo_obj.get_build_info(
            namespace, jenkins_url,
            pipeline_name, build_number)

        registry_url = build_info.get("REGISTRY_URL")
        # if its value is not "null", it will be used instead of registry_url
        registry_alias = build_info.get("REGISTRY_ALIAS")

        # possible values are ["success", "failed", "image_absent"]
        if status == "image_absent":
            body = self.image_absent_email_body()
        else:
            # convert status to boolean
            status = True if status == "success" else False

            # body should have repository name (without tag)
            body = self.body_of_email(
                status, image_name, registry_url, registry_alias)

        if registry_alias == "null":
            # registry name without ports for email subject prefix
            registry = build_info.get("REGISTRY_URL").strip().split(":")[0]
        else:
            # if registry_alias is not "null", use it for email subject prefix
            registry = registry_alias

        # format the subject of email
        if status and status != "image_absent":
            subject = self.weekly_success_subj.format(
                registry=registry, image_name=image_name)
        else:
            subject = self.weekly_failure_subj.format(
                registry=registry, image_name=image_name)

        # NOTIFY_CC_EMAILS list
        cc_emails = build_info.get("NOTIFY_CC_EMAILS", False)
        if cc_emails and cc_emails != "null":
            # convert comma separated emails to list of emails
            cc_emails = [e.strip() for e in cc_emails.strip(
            ).split(",") if e]
        else:
            cc_emails = []

        print ("Sending weekly scan email to {}".format(
            build_info.get("NOTIFY_EMAIL")))

        status, msg = self.sendemail_obj.email(
            build_info.get("SMTP_SERVER"),
            subject, body,
            build_info.get("FROM_ADDRESS"),
            [build_info.get("NOTIFY_EMAIL")],
            cc_emails)

        if status:
            print(msg)
        else:
            print("Failed to send email!")
            sys.exit(1)


if __name__ == "__main__":
    notify_object = WeeklyScanNotify()
    status = sys.argv[1].strip()
    namespace = sys.argv[2].strip()
    jenkins_url = sys.argv[3].strip()
    image_name = sys.argv[4].strip()
    build_number = sys.argv[5].strip()
    pipeline_name = sys.argv[6].strip()

    notify_object.notify(
        status, namespace, jenkins_url,
        image_name, build_number,
        pipeline_name)
