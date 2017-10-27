#!/usr/bin/env python

# FIXME: we've duplicated config.py from ../beanstalk_worker into this dir
# because we don't yet have a global config which can be shared across
# all components.
import config
import json
import logging
import os
import subprocess
import time
from urlparse import urljoin

import beanstalkc
from container_pipeline.lib.openshift import Openshift, OpenshiftError

config.load_logger()
logger = logging.getLogger('mail-service')

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("notify_user")

LOGS_DIR_PARENT = "/srv/pipeline-logs/"
LOGS_URL_BASE = "https://registry.centos.org/pipeline-logs/"
BUILD_LOGS_FILENAME = "build_logs.txt"
LINTER_STATUS_FILE = "linter_status.json"
SCANNERS_STATUS_FILE = "scanners_status.json"

SUCCESS_EMAIL_SUBJECT = "SUCCESS: Container build: %s is complete"
FAILURE_EMAIL_SUBJECT = "FAILED: Container build: %s is failed"
WEEKLY_EMAIL_SUBJECT = "Weekly scanning results for image: %s"

EMAIL_HEADER = ("CentOS Community Container Pipeline Service "
                "<https://github.com/centos/container-index>")

EMAIL_HEADER = EMAIL_HEADER + "\n" + "=" * (len(EMAIL_HEADER) - 22)

EMAIL_FOOTER = """
--
Do you have a query ?
Talk to Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline
"""

SUCCESS_EMAIL_MSG = """
Build status:\t\tSuccess
Image:\t\t\t%s
Build logs:\t\t%s
Cause of build:\t\t%s
"""

FAILURE_EMAIL_MSG = """
Container build %s is failed due to error in build or test steps.

Build status:\t\tFailure
Build logs:\t\t%s
"""

LINTER_RESULTS = """
Dockerfile linter results:

%s
"""

SCANNERS_RESULTS = """
Atomic scanners results for built image %s

%s
"""


class NotifyUser(object):
    "Compose and send build status, linter and scanners results"

    def __init__(self, job_info):

        self.send_mail_command = "/opt/cccp-service/mail_service/send_mail.sh"
        self.job_info = job_info

        # the logs directory
        self.logs_dir = os.path.join(
            LOGS_DIR_PARENT,
            self.job_info["test_tag"])

        # linter execution status file
        self.linter_status_file = os.path.join(
            self.logs_dir, LINTER_STATUS_FILE)

        # scanners execution status file
        self.scanners_status_file = os.path.join(
            self.logs_dir, SCANNERS_STATUS_FILE)

        # if image has successful build
        if self.job_info.get("build_status"):
            logger.debug("Processing mail for SUCCESS build.")
            self.image_under_test = job_info.get("output_image")

            # for eg: the value would be
            # registry.centos.org/nshaikh/scanner-rpm-verify:latest
            self.project = self.image_under_test.replace(
                "registry.centos.org/", "")

        # if it is weekly scan job
        elif self.job_info.get("weekly"):
            logger.debug("Processing mail for Weekly scan.")
            self.image_under_test = job_info.get("output_image")
            # for eg: the value would be
            # registry.centos.org/nshaikh/scanner-rpm-verify:latest
            self.project = self.image_under_test.replace(
                "registry.centos.org/", "")

        # if it is a failed build
        else:
            logger.debug("Processing mail for failed build.")
            self.image_under_test = job_info.get("project_name")
            # projet_name / self.image_under_test and self.project are same
            self.project = job_info.get("project_name")

        # build_logs filename
        self.build_logs = urljoin(
            LOGS_URL_BASE,
            self.job_info["test_tag"],
            BUILD_LOGS_FILENAME
        )

        self.openshift = Openshift(logger=logger)

    def _escape_text_(self, text):
        "Escapes \n,\t with \\n,\\tt for rendering in email body"

        return text.replace("\n", "\\n").replace("\t", "\\t")

    def update_subject_of_email(self, subject):
        """
        Mail server container is created with a environment variable
        "ENVIRONMENT", its value should be among [production,pre-prod,test].
        If given production as value, the subject is kept intact, else
        the value is pre-pended with the subject. Like [test] SUCCESS [..]
        """
        deployment = os.environ.get("DEPLOYMENT", False)

        logger.debug("Got environment variable DEPLOYMENT=%s", deployment)
        # if environment variable is not found, consider production
        if not deployment:
            return subject

        # case insensitive check for string 'production'
        elif deployment.strip().lower() == "production":
            # default is production environment
            return subject
        else:
            return "[" + deployment + "] " + subject

    def send_email(self, subject, contents):
        "Sends email to user"

        # process subject of email based on if it is production or not
        subject = self.update_subject_of_email(subject)

        subprocess.call([
            self.send_mail_command,
            subject,
            self.job_info["notify_email"],
            self._escape_text_(contents)])

    def _read_status(self, filepath):
        "Method to read status JSON files"
        try:
            fin = open(filepath)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
                           (filepath, str(e)))
            return None
        else:
            return json.load(fin)

    def _read_text_file(self, text_file):
        "Method to read text files"

        try:
            fin = open(text_file)
        except IOError as e:
            logger.warning("Failed to read %s file, error: %s" %
                           (text_file, str(e)))
            return None
        else:
            return fin.read()

    def _dump_logs(self, logs, logfile):
        "Method to dump logs into logfile"

        try:
            # open in append mode, if there are more logs already
            fin = open(logfile, "a+")
        except IOError as e:
            logger.warning("Failed to open %s file in append mode. Error: %s"
                           % (logfile, str(e)))
        else:
            fin.write(logs)

    def _separate_section(self, char="-", count=99):
        " Creates string with char x count and returns"

        return char * count

    def compose_email_subject(self):
        " Composes email subject based on build status"

        if self.job_info.get("build_status"):
            return SUCCESS_EMAIL_SUBJECT % self.project
        else:
            return FAILURE_EMAIL_SUBJECT % self.project

    def compose_success_build_contents(self):
        "Composes email contents for completed builds"

        # need output image name and build logs
        return SUCCESS_EMAIL_MSG % (
            self.job_info["output_image"],
            self.build_logs,
            self.job_info["cause_of_build"])

    def compose_failed_build_contents(self):
        "Composes email contents for email of failed build"

        # need output image name and build logs
        return FAILURE_EMAIL_MSG % (
            self.project,
            self.build_logs)

    def compose_scanners_summary(self):
        "Composes scanners result summary"

        scanners_status = self._read_status(self.scanners_status_file)
        if not scanners_status:
            # TODO: Better handling and reporting here
            return ""

        text = ""
        for scanner in scanners_status["logs_file_path"]:
            text += scanner + ":\n"
            text += scanners_status["msg"][scanner] + "\n"
            text += "Detailed logs link: "
            text += scanners_status["logs_URL"][scanner]
            text += "\n\n"

        return SCANNERS_RESULTS % (self.image_under_test, text)

    def compose_linter_summary(self):
        "Composes Dockerfile Linter results summary"

        linter_status = self._read_status(self.linter_status_file)
        if not linter_status:
            # TODO: Better handling and reporting here
            return ""

        if not linter_status["lint_status"]:
            # TODO: Better handling and reporting here
            return ""

        linter_results = self._read_text_file(
            linter_status["linter_results_path"])

        if not linter_results:
            # TODO: Better handling and reporting here
            return ""

        return LINTER_RESULTS % linter_results

    def compose_email_contents(self):
        "Aggregates contents from different modules and composes one email"

        text = EMAIL_HEADER

        text += "\n"

        # if build has failed
        if not self.job_info.get("build_status"):
            text += self.compose_failed_build_contents()
            # see if job_info has logs keyword and append those logs to
            # build_logs
            if self.job_info.get("logs"):
                # build_logs.txt file path on the disk
                logfile = os.path.join(self.logs_dir, BUILD_LOGS_FILENAME)
                self._dump_logs(str(self.job_info.get("logs")), logfile)

        else:
            text += self.compose_success_build_contents()

            # scanners will run only on success builds
            # new line and separate section with hyphens
            text += "\n" + self._separate_section()

            # scanners results
            text += self.compose_scanners_summary()

        # linter has already run for project irrespective of
        # build failure or success

        # new line and separate section with hyphens
        text += "\n" + self._separate_section()

        # linter results
        text += self.compose_linter_summary()

        # put email footer
        text += EMAIL_FOOTER

        return text

    def compose_weekly_email(self):
        "Compose weekly scanning email artifcats"

        subject = WEEKLY_EMAIL_SUBJECT % self.image_under_test
        text = EMAIL_HEADER + "\n" + self.compose_scanners_summary() +\
            EMAIL_FOOTER
        return subject, text

    def notify_user(self):
        """
        Main method to orchestrate the email body composition
        and sending email
        """
        if self.job_info.get("weekly"):
            subject, email_contents = self.compose_weekly_email()
            self.remove_status_files([self.scanners_status_file])
        else:
            subject = self.compose_email_subject()
            email_contents = self.compose_email_contents()
            self.remove_status_files([
                self.linter_status_file,
                self.scanners_status_file])
        # send email
        logger.info("Sending email to user %s" %
                    self.job_info["notify_email"])
        self.send_email(subject, email_contents)

        """
        This is for cleaning up the openshift envrionment after the build
        is over. We are putting some delay so that the built image is
        pushed to registry properly and it does not give error while deleting
        """
        time.sleep(50)
        try:
            self.openshift.delete(self.job_info['project_hash_key'])
        except Exception as e:
            logger.critical("Failed to delete OpenShift project: {} error: {}"
                            .format(self.job_info['project_name'], e))

        # if it is a weekly scan, return True to delete service_debug_log.txt
        if self.job_info.get("weekly", False):
            return True
        # if build status if False, do not delete service_debug_log.txt
        return self.job_info.get("build_status", False)

    def remove_status_files(self, status_files):
        "Removes the status file"
        logger.debug("Cleaning statuses files %s" % str(status_files))
        for each in status_files:
            try:
                os.remove(each)
            except OSError as e:
                logger.info("Failed to remove file: %s , error: %s" %
                            (each, str(e)))


while True:
    logger.debug("Listening to notify_user tube")
    job = bs.reserve()
    job_id = job.jid
    job_info = json.loads(job.body)
    dfh = config.DynamicFileHandler(
        logger,
        os.path.join(job_info['logs_dir'], config.SERVICE_LOGFILE))
    logger.info("Received Job: {}".format(str(job_info)))
    try:
        notify_user = NotifyUser(job_info)
        build_status = notify_user.notify_user()
    except Exception as e:
        logger.critical(
            "Mail server could not process the job: {} with error : {}"
            .format(str(job_info), e))
    finally:
        job.delete()
        dfh.remove()

    # This cleans the per build logs file created for the build
    # If service returned properly after sending email, the file
    # will be cleaned, if service raises, the file statys for debugging
    if build_status:
        dfh.clean()
