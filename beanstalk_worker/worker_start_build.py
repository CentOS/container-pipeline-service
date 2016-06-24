#!/usr/bin/env python

import beanstalkc
import json
import os
import re
import time
from DependencyChecker import DependencyChecker


bs = beanstalkc.Connection(host="openshift")
bs.watch("start_build")
bs.use("failed_build")

while True:
  print "listening to start_build tube"
  job = bs.reserve()
  jobid = job.jid
  job_details = json.loads(job.body) 
  
  print "==> Retrieving namespace"
  name = job_details['name']
  tag = job_details['tag']
  depends_on = job_details['depends_on']
  
  print "==> check dependencies are available or not"
  dependency_present = False
  if depends_on = None:
    dependency_present = True

  dc = DependencyChecker()
  while dependency_present != True
    dependency_present = dc.checkdependencies(depends_on)
    time.sleep(30)

  print "==> Login to openshift server"
  command = "oc login https://openshift:8443 -u test-admin -p test --certificate-authority=./ca.crt"
  os.system(command)
  
  print "==> change project to the desired one"
  command = "oc project "+name+"-"+tag
  os.system(command)
  
  print "==> start the build"
  command = "oc --namespace "+name+"-"+tag+" start-build build"
  build_details = os.popen(command).read().rstrip()
  print "build started is "+build_details 
  
  status_command = "oc get --namespace "+name+"-"+tag+" build/"+build_details+"|grep -v STATUS"
  is_running = 1
  
  print "==> Checking the build status"
  while is_running >= 0:
    status= os.popen(status_command).read()
    is_running = re.search("New|Pending|Running",status)
    print "current status: "+status
    time.sleep(30)

  is_complete=os.popen(status_command).read().find('Complete')
  
  print "==>If build is successful delete the job else put it to failed build tube"
  if is_complete < 0:
     bs.put(json.dumps(job_details))

  job.delete()
