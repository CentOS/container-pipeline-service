#!/usr/bin/env python

import beanstalkc
import json
import subprocess
import re
import time
import smtplib

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("notify_user")

def send_mail(to_mail, subject, msg, logs):
    if(logs != null):
        failed_msg_command = "/mail_service/send_failed_mail.sh"
        logfile = open("/tmp/failed_log.log","w")
        logfile.write(logs)
        logfile.close()
        subprocess.call([failed_msg_command,subject,to_mail,"/tmp/failed_log.log"])
    else:
        success_msg_command = "mail_service/send_success_mail.sh"
        subprocess.call([success_msg_command,subject,to_mail,msg])
#    SERVER = "localhost"
#    FROM = "container-build-report@centos.org"
#    TO = [to_mail] # must be a list
#    SUBJECT = subject
#    TEXT = msg+"\n"+logs

    # Prepare actual message

#    message = """\
#    From: %s
#    To: %s
#    Subject: %s

#    %s
#    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)

    # Send the mail
#    server = smtplib.SMTP(SERVER)
#    server.sendmail(FROM, TO, message)
#   server.quit()

while True:
    print "listening to notify_user tube"
    job = bs.reserve()
    jobid = job.jid
    job_details = json.loads(job.body)

    print "==> Retrieving message details"
    to_mail = job_details['to_mail']
    subject = job_details['subject']
    msg = job_details['msg']
    logs = job_details['logs']

    print "==> sending mail to user"
    send_mail(to_mail, subject, msg, logs)

    job.delete()
