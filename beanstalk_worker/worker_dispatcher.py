#!/usr/bin/env python

import beanstalkc
import json
import os
import re
import time

bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("master_tube")

while True:
  print "listening to master_tube"
  job = bs.reserve()
  job_details = json.loads(job.body)

  print "==> Retrieving job action"
  action = job_details['action']

  if action == "start_build":
    bs.use("start_build")
    bs.put(json.dumps(job_details))
    print "==> Job moved to build tube"
  elif action == "start_scan":
    bs.use("start_scan")
    bs.put(json.dumps(job_details))
    print "==> Job moved to test tube"
  elif action == "start_delivery":
    bs.use("start_delivery")
    bs.put(json.dumps(job_details))
    print "==> Job moved to delivery tube"
  elif action == "notify_user":
    bs.use("notify_user")
    bs.put(json.dumps(job_details))
    print "==> Job moved to notify tube"
  elif action == "report_scan_results":
    bs.use("report_scan_results")
    bs.put(json.dumps(job_details))
    print "==> Job moved to report scan results tube"
  elif action == "start_linter":
    bs.use("start_linter")
    bs.put(json.dumps(job_details))
    print "==> Job moved to linter tube"

  print "==> Deleting job"
  job.delete()
