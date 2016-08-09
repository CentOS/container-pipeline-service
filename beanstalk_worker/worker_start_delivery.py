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
bs.watch("start_delivery")
bs.use("delivery_failed")

logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
)
ch.setFormatter(formatter)
logger.addHandler(ch)


def start_delivery(job_details):
  try:
    logger.log(level=logging.INFO,msg="==> Retrieving namespace")
    name_space = job_details['name_space']
    #tag = job_details['tag']
    #build_tag = job_details['build_tag']
  
    logger.log(level=logging.INFO,msg="==> Login to openshift server")
    command = "oc login https://openshift:8443 -u test-admin -p test --certificate-authority=./ca.crt"
    os.system(command)
  
    logger.log(level=logging.INFO,msg="==> change project to the desired one")
    command = "oc project "+name_space
    os.system(command)
  
    logger.log(level=logging.INFO,msg="==> start the build")
    command = "oc --namespace "+name_space+" start-build delivery"
    build_details = os.popen(command).read().rstrip()
    if build_details=="":
      logger.log(level=logging.CRITICAL,msg="Delivery could not be started due to error communicating openshift")
      return 1
    logger.log(level=logging.INFO,msg="delivery started is "+build_details)
  
    status_command = "oc get --namespace "+name_space+" build/"+build_details+"|grep -v STATUS"
    is_running = 1
  
    logger.log(level=logging.INFO,msg="==> Checking the delivery status")
    while is_running >= 0:
        status= os.popen(status_command).read()
        is_running = re.search("New|Pending|Running",status)
        logger.log(level=logging.INFO,msg="current status: "+status)
        time.sleep(30)

    is_complete=os.popen(status_command).read().find('Complete')
  
    if is_complete < 0:
        bs.put(json.dumps(job_details))
        logger.log(level=logging.INFO,msg="==>Delivery is not successful putting it to failed delivery tube")
    return 0
  except Exception as e:
    logger.log(level=logging.FATAL, msg=e.message)
    return 1

while True:
  try:
    logger.log(level=logging.INFO,msg="listening to start_delivery tube")
    job = bs.reserve()
    job_details = json.loads(job.body) 
    result = start_delivery(job_details);
    if result == 0:
      logger.log(level=logging.INFO,msg="==>Delivery is successful deleting the job")
      job.delete()
    else:
      logger.log(level=logging.INFO, msg="Job was not succesfull and returned to tube")
  except Exception as e:
    logger.log(level.FATAL, msg=e.message)
