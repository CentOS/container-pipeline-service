#!/usr/bin/env python

import beanstalkc
import json
import os
import re
import time
from DependencyChecker import DependencyChecker


bs = beanstalkc.Connection(host="openshift")
bs.watch("master_tube")

while True:
  print "listening to master_tube"
  job = bs.reserve()
  job_details = json.loads(job.body) 
  
  print "==> Retrieving job action"
  action = job_details['action']

  if action == "start_build" :
    bs.use("start_build")
    bs.put(json.dumps(job_details))
  elif action == "start_test" :
    bs.use("start_test")
    bs.put(json.dumps(job_details))
  elif action = "start_delivery" :
    bs.use("start_delivery")
    bs.put(json.dumps(job_details))
  elif action = "notify_user"
    bs.use("notify_user")
    bs.put(json.dumps(job_details))
  
  print "==> job moved to specific tube"
  job.delete()
