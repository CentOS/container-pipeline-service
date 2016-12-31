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

config_path = os.path.dirname(os.path.realpath(__file__))
kubeconfig = " --config=" + os.path.join(config_path, "node.kubeconfig")

DEBUG = 1
DELAY = 30

def debug_log(msg):
    if DEBUG == 1:
        logger.log(level=logging.DEBUG, msg=msg)


def run_command(command):
    try:
        p = Popen(command, bufsize=0, shell=True,
              stdout=PIPE, stderr=PIPE, stdin=PIPE)
        p.wait()
        out,err = p.communicate()
        return out
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        return e.message

def notify_build_failure(namespace, notify_email, logs):
    msg_details = {}
    msg_details['action'] = 'notify_user'
    msg_details['subject'] = "FAILED: Container-build failed " + namespace
    msg_details['msg'] = "Container build for " + namespace + \
        " is failed due to error in build or test steps. Pleae check attached logs"
    msg_details['logs'] = logs
    msg_details['notify_email'] = notify_email
    bs.use('master_tube')
    bs.put(json.dumps(msg_details))


def start_build(job_details):
    try:
        debug_log(" Retrieving namespace")
        appid = job_details['appid']
        jobid = job_details['jobid']
        desired_tag = job_details['desired_tag']
        namespace = appid + "-" + jobid + "-" + desired_tag
        #depends_on = job_details['depends_on']
        notify_email = job_details['notify_email']

        debug_log("Login to OpenShift server")
        command_login = "oc login https://OPENSHIFT_SERVER_IP:8443 -u test-admin -p test" + \
            kubeconfig + " --certificate-authority=" + config_path + "/ca.crt"
        out = run_command(command_login)
        debug_log(out)

        debug_log(" change project to the desired one")
        command_change_project = "oc project " + namespace + kubeconfig
        out = run_command(command_change_project)
        debug_log(out)

        debug_log("start the build")
        command_start_build = "oc --namespace " + namespace + \
            " start-build build" + kubeconfig
        out = run_command(command_start_build)
        debug_log(out)

        build_details = out.split('"')[1].rstrip()
        debug_log(build_details)

        if build_details == "":
            logger.log(level=logging.CRITICAL,
                       msg="build could not be started as OpenShift is not reachable")
            return 1

        debug_log("build started is " + build_details)

        status_command = "oc get --namespace " + namespace + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1

        debug_log("Checking the build status")
        while is_running >= 0:
            status = run_command(status_command).rstrip()
            is_running = re.search("New|Pending|Running", status)
            debug_log("current status: " + status)
            time.sleep(DELAY)

        is_complete = run_command(status_command).find('Complete')

        # checking logs for the build phase
        log_command = "oc logs --namespace " + namespace + " build/" + \
            build_details + kubeconfig
        try:
            logs = run_command(log_command)
        except Exception as e:
            logger.log(level=logging.CRITICAL, msg=e.message)
            logs = "Could not retrieve build logs"

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            notify_build_failure(namespace, notify_email, logs)
            debug_log("Build is not successful putting it to failed build tube")
        else:
            debug_log("Build is successfull going for next job")

        return 0
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        return 1

while True:
    try:
        debug_log("listening to start_build tube")
        current_jobs_in_tube = int(dict(item.split(":") for item in bs.stats_tube('start_build').split('\n')[1:-1])['current-jobs-ready'])
        if current_jobs_in_tube > 0 :
            job = bs.reserve()
            job_details = json.loads(job.body)
            result = start_build(job_details)
            job.delete()
        else:
            debug_log("No job found to process looping again")
            time.sleep(DELAY)
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        time.sleep(DELAY)
