#!/usr/bin/env python

import beanstalkc
import json
import subprocess
import re
import time
import smtplib

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("notify_user")


def send_mail(notify_email, subject, msg, logs):
    if(logs is not None):
        failed_msg_command = "/mail_service/send_failed_mail.sh"
        logfile = open("/tmp/build_log.log", "w")
        logfile.write(logs)
        logfile.close()
        subprocess.call(
            [failed_msg_command,
             subject,
             notify_email,
             msg,
             "/tmp/build_log.log"])
    else:
        success_msg_command = "/mail_service/send_success_mail.sh"
        subprocess.call([success_msg_command, subject, notify_email, msg])


def notify_user_with_scan_results(job_info):
    """
    Fetches the results of scanners from job_info and
    composes the the message body to be sent to the user.
    """
    print "==> Retrieving message details.."
    notify_email = job_info['notify_email']

    # find image's full name and append the desired tag
    image_under_test = job_info.get('name').split(":")[1]

    print "==> Image under test is %s" % image_under_test

    subject = "Scanning results for image: %s" % image_under_test
    text = """
CentOS Community Container Pipeline Service <https://wiki.centos.org/ContainerPipeline>
=======================================================================================

Container image scanning results for image=%s built at CCCP.

Following are the atomic scanners ran on built image, displaying the result message and detailed logs.

"""

    for scanner in job_info["msg"]:
        text += scanner + ":\n"
        text += job_info["msg"][scanner]
        text += "\n\n"

    text += "Detailed logs per scanner:\n\n"
    for scanner in job_info["logs"]:
        text += json.dumps(
                job_info["logs"][scanner],
                indent=4,
                sort_keys=True)
        text += "\n\n"

    print "==> Sending scan results email to user: %s" % notify_email
    # last parameter (logs) has to None for the sake of
    # condition put in send_mail function
    send_mail(notify_email, subject, text, None)

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
    print "==> Put job for delivery on master tube with id = %s" % job_id


while True:
    print "Listening to notify_user tube"

    job = bs.reserve()
    job_id = job.jid
    job_info = json.loads(job.body)

    if "scan_results" in job_info:
        if job_info["scan_results"]:
            print "==> Received job id= %s for reporting scan results" % job_id
            notify_user_with_scan_results(job_info)
            job.delete()
            continue

    print "==> Retrieving message details"
    notify_email = job_info['notify_email']
    subject = job_info['subject']

    if 'msg' not in job_info:
        msg = None
    else:
        msg = job_info['msg']

    if 'logs' not in job_info:
        logs = None
    else:
        logs = job_info['logs']

    print "==> Sending email to user"
    send_mail(notify_email, subject, msg, logs)
    job.delete()
