#!/usr/bin/env python

import beanstalkc
import json
import os
import re
import time
from DependencyChecker import DependencyChecker
import logging
import sys


bs = beanstalkc.Connection(host="openshift")
bs.watch("start_build")
bs.use("failed_build")

logger = logging.getLogger("pipeline-build-worker")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

command_path = sys.argv[0]
logger.log(level=logging.INFO,msg="Getting kubeconfig path"+command_path)

def start_build(job_details):
  try:
    logger.log(level=logging.INFO,msg="==> Retrieving namespace")
    name = job_details['name']
    tag = job_details['tag']
    depends_on = job_details['depends_on']
  
    #print "==> check dependencies are available or not"
    #dependency_present = False
    #if depends_on == None:
    #  dependency_present = True

    #dc = DependencyChecker()
    #while dependency_present != True
    #  dependency_present = dc.checkdependencies(depends_on)
    #  time.sleep(30)

    logger.log(level=logging.INFO, msg="==> Login to openshift server")
    command = "oc login https://openshift:8443 -u test-admin -p test --config=node.kubeconfig --certificate-authority=ca.crt"
    os.system(command)
  
    logger.log(level=logging.INFO, msg="==> change project to the desired one")
    command = "oc project "+name+"-"+tag
    os.system(command)
  
    logger.log(level=logging.INFO, msg="==> start the build")
    command = "oc --namespace "+name+"-"+tag+" start-build build"
    build_details = os.popen(command).read().rstrip()
    if build_details=="":
      logger.log(level=logging.CRITICAL, msg="build could not be started as openshift is not reachable")
      return 1

    logger.log(level=logging.INFO, msg="build started is "+build_details)

    status_command = "oc get --namespace "+name+"-"+tag+" build/"+build_details+"|grep -v STATUS"
    is_running = 1

    logger.log(level=logging.INFO, msg="==> Checking the build status")
    while is_running >= 0:
      status= os.popen(status_command).read()
      is_running = re.search("New|Pending|Running",status)
      logger.log(level=logging.INFO, msg="current status: "+status)
      time.sleep(30)

    is_complete=os.popen(status_command).read().find('Complete')

    if is_complete < 0:
      bs.put(json.dumps(job_details))
      logger.log(level=logging.INFO, msg="==>Build is not successful putting it to failed build tube")

    return 0
  except Exception as e:
    logger.log(level=logging.CRITICAL, msg=e.message)
    return 1

while True:
  try:
    logger.log(level=logging.INFO, msg="listening to start_build tube")
    job = bs.reserve()
    job_details = json.loads(job.body) 
    result = start_build(job_details)
    if result == 0:
      logger.log(level=logging.INFO, msg="==>Build is successful deleting the job")
      job.delete()
    else:
      logger.log(level=logging.INFO, msg="Job was not succesfull and returned to tube")
  except Exception as e:
    logger.log(level.CRITICAL, msg=e.message)
