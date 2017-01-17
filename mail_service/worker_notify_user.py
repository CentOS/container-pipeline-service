#!/usr/bin/env python

import beanstalkc
import json
import subprocess

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
        # escape the \ with \\ for rendering in email
        msg = msg.replace("\n", "\\n")
        subprocess.call([success_msg_command, subject, notify_email, msg])


def notify_user_with_scan_results(job_info):
    """
    Fetches the results of scanners from job_info and
    composes the the message body to be sent to the user.
    """
    print "==> Retrieving message details.."
    notify_email = job_info['notify_email']

    # find image's full name, remove the registry name
    image_under_test = job_info.get('name').split(":")[1]
    # remove the port of registry
    # TODO: Find a better way to remove regisry and port part
    image_under_test = image_under_test.replace("5000/", "")

    print "==> Image under test is %s" % image_under_test

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

    print "==> Sending scan results email to user: %s" % notify_email
    # last parameter (logs) has to None for the sake of
    # condition put in send_mail function
    send_mail(notify_email, subject, text, None)

    # if weekly scan is being executed, we do not want trigger delivery phase
    if job_info.get("weekly"):
        print "Weekly scan completed; moving to next job."
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
    print "==> Put job for delivery on master tube with id = %s" % job_id


def notify_user_with_linter_results(job_info):
    """
    Fetches the results of linter from job_info and composes the the message
    body to be sent to the user.
    """
    print "==> Retrieving message details.."
    notify_email = job_info['notify_email']
    project = job_info["namespace"] + "/" + job_info["job_name"]

    subject = "Dockerfile linter results for project: %s" % project
    if "logs" not in job_info:
        # Linter failed for some reason which should be in "msg" key
        text = "Failed to scan the Dockerfile for project %s \n" % project
        text += "Reason for failure: %s\n" % job_info["msg"]

        print "==> Sending linter failure results email to user: %s" \
            % notify_email
        # Setting last parameter to anything but None should trigger failure
        # email
        send_mail(notify_email, subject, text, logs=job_info.get("msg"))
    else:
        text = """
CentOS Community Container Pipeline Service <https://wiki.centos.org/ContainerPipeline>
=======================================================================================

Dockerfile linter results for project=%s.

""" % project

        text += "Detailed linter logs:\n\n"
        text += job_info["logs"] + "\n\n"

        print "==> Sending linter results email to user: %s" % notify_email
        # last parameter (logs) has to None for the sake of
        # condition put in send_mail function
        send_mail(notify_email, subject, text, None)


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

    if "linter_results" in job_info:
        if job_info["linter_results"]:
            print "==> Received job id= %s for reporting linter results" \
                % job_id
            notify_user_with_linter_results(job_info)
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
