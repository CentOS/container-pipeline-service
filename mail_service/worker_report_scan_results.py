#!/usr/bin/env python

import beanstalkc
import json
import subprocess
import re
import time

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("report_scan_results")

while True:
  print "==> Listening to report_scan_results tube"
  job = bs.reserve()
  job_id = job.jid
  job_info = json.loads(job.body)
  print "==> Received job id= %s for reporting scan results" % job_id

  print "==> Retrieving message details.."
  notify_email = job_info['notify_email']

  # find image's full name and append the desired tag
  image_under_test = job_info.get('name').split(":")[0] + ":" \
    + job_info.get("tag")
  print "==> Image under test is %s" % image_under_test

  subject = "Scanning results for image: %s" % image_under_test
  email_body = compose_email_text(job_details)

  print "==> Sending scan results to user %s " % notify_email
  command = "/mail_service/send_mail.sh"
  subprocess.call([
      command,
      subject,
      email_body,
      notify_email,
      ])

  # We notified user, lets put the job on delivery tube
  # all other details about job stays same
  next_job = job_info
  # change the action
  next_job["action"] = "start_delivery"

  # Remove the msg and logs from the job_info as they are not needed now
  next_job.pop("msg")
  next_job.pop("logs")

  # Put the job details on central tube
  bs.use("master_tube")
  job_id = bs.put(json.dumps(next_job))
  logger.log(
    level=logging.INFO,
    msg="Put job for delivery on master tube with id = %s" % job_id
    )


def compose_email_text(job_info):
    """
    Fetches the results of scanners from job_info and
    composes the the message body to be sent to the user.
    """
    text = "Scanning results :\n\n"

    for scanner in job_info["msg"]:
        text += scanner + ":\n"
        text += job_info["msg"]["scanner"]
        text += "\n\n"

    text = "Detailed logs per scanner:\n\n"
    for scanner in job_info["logs"]:
        text += json.dumps(
                job_info["logs"][scanner],
                indent=4,
                sort_keys=True)
        text += "\n\n"

    return text
