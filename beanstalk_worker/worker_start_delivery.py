#!/usr/bin/env python

import beanstalkc
import json
from subprocess import Popen
from subprocess import PIPE
import re
import time
import logging
import sys
import os

bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("start_delivery")
bs.use("delivery_failed")

logger = logging.getLogger("pipeline-delivery-worker")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

config_path = os.path.dirname(os.path.realpath(__file__))
kubeconfig = " --config=" + os.path.join(config_path, "node.kubeconfig")

DEBUG = 1


def notify_build_failure(name_space, notify_email, logs):
    msg_details = {}
    msg_details['action'] = 'notify_user'
    msg_details['subject'] = "FAILED: Container-build failed " + name_space
    msg_details['msg'] = "Container build " + name_space + \
        " failed due to error in build or test steps. Pleae check attached logs"
    msg_details['logs'] = logs
    msg_details['notify_email'] = notify_email
    bs.use('master_tube')
    bs.put(json.dumps(msg_details))


def debug_log(msg):
    if DEBUG == 1:
        logger.log(level=logging.INFO, msg=msg)


def run_command(command):
    try:
        p = Popen(command, bufsize=0, shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)
        #p.wait()
        out = p.communicate()
        return out
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        return e.message


def start_delivery(job_details):
    try:
        debug_log("Retrieving namespace")
        name_space = job_details['name_space']
        notify_email = job_details['notify_email']

        #tag = job_details['tag']
        #depends_on = job_details['depends_on']

        debug_log("Login to OpenShift server")
        command_login = "oc login https://OPENSHIFT_SERVER_IP:8443 -u test-admin -p test" + \
            kubeconfig + " --certificate-authority=" + config_path + "/ca.crt"
        out = run_command(command_login)
        debug_log(out)

        debug_log(" change project to the desired one")
        command_change_project = "oc project " + name_space + kubeconfig
        out = run_command(command_change_project)
        debug_log(out)

        debug_log("start the delivery")
        command_start_build = "oc --namespace " + name_space + \
            " start-build delivery" + kubeconfig
        out = run_command(command_start_build)
        debug_log(out)

        build_details = out[0].split('"')[-1].rstrip()
        debug_log(build_details)

        if build_details == "":
            logger.log(level=logging.CRITICAL,
                       msg="build could not be started as OpenShift is not reachable")
            return 1

        debug_log("Delivery started is " + build_details)

        status_command = "oc get --namespace " + name_space + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1

        debug_log("Checking the delivery status")
        while is_running >= 0:
            status = run_command(status_command)[0].rstrip()
            is_running = re.search("New|Pending|Running", status)
            debug_log("current status: " + status)
            time.sleep(30)

        is_complete = run_command(status_command)[0].find('Complete')
        # checking logs for the build phase
        log_command = "oc logs --namespace " + name_space + " build/" + \
            build_details + kubeconfig
        logs = run_command(log_command)
        logs = logs[0]

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            notify_build_failure(name_space, notify_email, logs)
            debug_log(
                "Delivery is not successful putting it to failed build tube")

        return 0
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        return 1

while True:
    try:
        debug_log("listening to start_delivery tube")
        job = bs.reserve()
        job_details = json.loads(job.body)
        result = start_delivery(job_details)
        if result == 0:
            debug_log("Delivery is successful deleting the job")
            job.delete()
        else:
            debug_log("Job was not succesfull and returned to tube")
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
