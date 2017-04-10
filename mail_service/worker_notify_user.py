#!/usr/bin/env python

import beanstalkc
import json
import logging
import subprocess
# FIXME: we've duplicated config.py from ../beanstalk_worker into this dir
# because we don't yet have a global config which can be shared across
# all components.
from config import load_logger

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("notify_user")

LOGS_DIR = "/srv/pipeline-logs/"
LOGS_URL_BASE = "https://registry.centos.org/pipeline-logs/"

load_logger()
logger = logging.getLogger('mail-service')


def send_mail(notify_email, subject, msg):
    """
    Sends user success build notification
    """
    success_msg_command = "/mail_service/send_mail.sh"
    # escape the \ with \\ for rendering in email
    msg = msg.replace("\n", "\\n")
    subprocess.call([success_msg_command, subject, notify_email, msg])


def notify_user_with_scan_results(job_info):
    """
    Fetches the results of scanners from job_info and
    composes the the message body to be sent to the user.
    """
    logger.debug("Retrieving message details from: %s" % job_info)
    notify_email = job_info['notify_email']

    # find image's full name, remove the registry name
    image_under_test = job_info.get('name').split(":")[1]
    # remove the port of registry
    # TODO: Find a better way to remove regisry and port part
    image_under_test = image_under_test.replace("5000/", "")

    logger.debug("Image under test is %s" % image_under_test)

    if job_info.get("weekly"):
        subject = "Weekly scanning results for image: %s" % image_under_test
    else:
        subject = "Scanning results for image: %s" % image_under_test
    text = """
CentOS Community Container Pipeline Service <https://wiki.centos.org/ContainerPipeline>
==================================================================

Container image scanning results for image=%s built at CentOS community container pipeline service.

Following are the atomic scanners ran on built image, displaying the result message and detailed logs.

"""
    # render image_under_test from above text
    text = text % image_under_test

    for scanner in job_info["msg"]:
        text += scanner + ":\n"
        text += job_info["msg"][scanner]
        text += "\n\n"

    text += "Detailed logs per scanner:\n\n"
    for scanner in job_info["logs"]:
        text += job_info["logs"][scanner]
        text += "\n\n"

    logger.info("Sending scan results email to user: %s" % notify_email)
    logger.debug('Scan results email content: %s\n%s' % (subject, text))
    # last parameter (logs) has to None for the sake of
    # condition put in send_mail function
    send_mail(notify_email, subject, text)

    # if weekly scan is being executed, we do not want trigger delivery phase
    if job_info.get("weekly"):
        logger.info("Weekly scan completed; moving to next job.")
        return

    # We notified user, lets put the job on delivery tube
    # all other details about job stays same
    next_job = job_info
    # change the action
    next_job["action"] = "start_delivery"

    # Remove the msg and logs from the job_info as they are not needed now
    next_job.pop("msg")
    next_job.pop("logs")
    next_job.pop("scan_results")

    # Put the job details on central tube
    bs.use("master_tube")
    job_id = bs.put(json.dumps(next_job))
    logger.info("Put job for delivery on master tube with id = %s" % job_id)


def notify_user_with_linter_results(job_info):
    """
    Fetches the results of linter from job_info and composes the the message
    body to be sent to the user.
    """
    logger.debug("Retrieving message details from %s" % job_info)
    notify_email = job_info['notify_email']
    project = job_info["namespace"] + "/" + job_info["job_name"]

    subject = "Dockerfile linter results for project: %s" % project
    if "logs" not in job_info:
        # Linter failed for some reason which should be in "msg" key
        text = "Failed to scan the Dockerfile for project %s \n" % project
        text += "Reason for failure: %s\n" % job_info["msg"]

        logger.info("Sending linter failure results email to user: %s"
                    % notify_email)
        logger.debug("Linter failure results email content: %s\n%s"
                     % (subject, text))
        # Setting last parameter to anything but None should trigger failure
        # email
        send_mail(notify_email, subject, text)
    else:
        text = """
CentOS Community Container Pipeline Service <https://wiki.centos.org/ContainerPipeline>
=======================================================================================

Dockerfile linter results for project=%s.

""" % project

        text += "Detailed linter logs:\n\n"
        text += job_info["logs"] + "\n\n"

        logger.info(
            "Sending linter results email to user: %s" % notify_email)
        logger.debug("Linter results email content: %s\n%s"
                     % (subject, text))
        # last parameter (logs) has to None for the sake of
        # condition put in send_mail function
        send_mail(notify_email, subject, text)


while True:
    logger.info("Listening to notify_user tube")

    job = bs.reserve()
    job_id = job.jid
    job_info = json.loads(job.body)

    if "scan_results" in job_info:
        if job_info["scan_results"]:
            logger.info("Received job id= %s for reporting scan results"
                        % job_id)
            notify_user_with_scan_results(job_info)
            job.delete()
            continue

    if "linter_results" in job_info:
        if job_info["linter_results"]:
            logger.info("Received job id= %s for reporting linter results"
                        % job_id)
            notify_user_with_linter_results(job_info)
            job.delete()
            continue

    if "build_failed" in job_info:
        if job_info["build_failed"]:
            logger.info("Build with id= %s failed, sending failure email."
                        % job_id)

            logs_url = job_info["build_logs_file"].replace(
                LOGS_DIR, LOGS_URL_BASE)

            subject = "FAILED: Container build failed " + job_info["namespace"]
            msg = """
Container build for %s is failed due to error in build or test
steps. Pleae check logs below.

Build logs: %s""" % (job_info["namespace"], logs_url)

            send_mail(job_info["notify_email"], subject, msg)
            job.delete()
            continue

    logger.info("Retrieving message details")
    notify_email = job_info['notify_email']
    subject = job_info['subject']

    if 'msg' not in job_info:
        msg = None
    else:
        msg = job_info['msg']

    logger.info("Sending email to user: %s" % notify_email)
    logger.debug('User email content: %s\n%s' % (subject, msg))
    send_mail(notify_email, subject, msg)

    job.delete()
