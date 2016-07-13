#!/usr/bin/env python

import beanstalkc
import json
import subprocess
import re
import time

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("notify_user")

while True:
  print "listening to notify_user tube"
  job = bs.reserve()
  jobid = job.jid
  job_details = json.loads(job.body) 
  
  print "==> Retrieving message details"
  to_mail = job_details['to_mail']
  subject = job_details['subject']
  msg = job_details['msg']
  
  print "==> sending mail to user"
  command = "/mail_service/send_mail.sh"
  subprocess.call([command,subject,msg,to_mail])
  
  job.delete()
