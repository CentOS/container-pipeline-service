#!/usr/bin/env python

import beanstalkc
import json
import subprocess
import re
import time

bs = beanstalkc.Connection(host="172.17.0.1")
bs.watch("start_build")
bs.use("failed_build")

while True:
  print "listening to start_build tube"
  job = bs.reserve()
  jobid = job.jid
  job_details = json.loads(job.body) 
  
  print "==> Retrieving namespace"
  to_mail = job_details['to_mail']
  msg = job_details['msg']
  attachment = job_details['attachment']
  
  print "==> Login to openshift server"
  command = "/mail_service/mail-config.sh"
  subprocess.call([command,msg,to_mail])
  
  job.delete()
