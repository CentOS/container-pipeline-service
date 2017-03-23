#!/usr/bin/env python

import beanstalkc
from binascii import hexlify
import hashlib
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
    debug_log("Running command: "+command)
    try:
        p = Popen(command, bufsize=0, shell=True,
              stdout=PIPE, stderr=PIPE, stdin=PIPE)
        #p.wait()
        out,err = p.communicate()
        return out
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        return e.message

def notify_build_failure(namespace, notify_email, build_logs_file):
    msg_details = {}
    msg_details['action'] = 'notify_user'
    msg_details['namespace'] = namespace
    msg_details['build_failed'] = True
    msg_details['notify_email'] = notify_email
    msg_details['build_logs_file'] = build_logs_file
    bs.use('master_tube')
    bs.put(json.dumps(msg_details))


def export_build_logs(logs, destination):
    """"
    Write logs in given destination
    """
    # to take care if the logs directory is not created
    if not os.path.exists(os.path.dirname(destination)):
        os.makedirs(os.path.dirname(destination))

    try:
        with open(destination, "w") as fin:
            fin.write(logs)
    except IOError as e:
        logger.log(level=logging.CRITICAL,
                   msg="Failed writing logs to %s" % destination)
        logger.log(level=logging.CRITICAL, msg=str(e))


def start_build(job_details):
    try:
        debug_log(" Retrieving namespace")
        appid = job_details['appid']
        jobid = job_details['jobid']
        desired_tag = job_details['desired_tag']
        namespace = str(appid) + "-" + str(jobid) + "-" + str(desired_tag)
        oc_name = hashlib.sha224(namespace).hexdigest()
        debug_log("Openshift project namespace is hashed from {0} to {1}, hash can be reproduced with sha224 tool"
                  .format(namespace, oc_name))
        #depends_on = job_details['depends_on']
        notify_email = job_details['notify_email']
        # This will be a mounted directory
        build_logs_file = os.path.join(
                job_details["logs_dir"],
                "build_logs.txt"
                )

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
        command_start_build = "oc --namespace " + oc_name + \
            " start-build build" + kubeconfig
        out = run_command(command_start_build)
        debug_log(out)

        build_details = out.split('"')[-1].rstrip()
        debug_log(build_details)

        if build_details == "":
            logger.log(level=logging.CRITICAL,
                       msg="build could not be started as OpenShift is not reachable")
            return 1

        debug_log("build started is " + build_details)

        status_command = "oc get --namespace " + oc_name + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1

        debug_log("Checking the build status")
        while is_running >= 0:
            status = run_command(status_command).rstrip()
            is_running = re.search("New|Pending|Running", status)
            debug_log("current status: " + status)
            time.sleep(DELAY)

        # checking logs for the build phase
        log_command = "oc logs --namespace " + oc_name + " build/" + \
            build_details + kubeconfig
        try:
            logs = run_command(log_command)
        except Exception as e:
            logger.log(level=logging.CRITICAL, msg=e.message)
            logs = "Could not retrieve build logs."
            logger.log(level=logging.CRITICAL, msg=logs)
        else:
            logger.log(level=logging.INFO,
                       msg="Writing build logs to NFS share..")
        finally:
            # Export logs on disk in either case
            export_build_logs(logs, build_logs_file)

        is_complete = run_command(status_command).find('Complete')

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            notify_build_failure(namespace, notify_email, build_logs_file)
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
        else:
            debug_log("No job found to process looping again")
            time.sleep(DELAY)
    except Exception as e:
        logger.log(level=logging.CRITICAL, msg=e.message)
        time.sleep(DELAY)
    finally:
        job.delete()
