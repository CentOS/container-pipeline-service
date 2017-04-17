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
import config


bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("start_delivery")
bs.use("delivery_failed")

config.load_logger()
logger = logging.getLogger("delivery-worker")

config_path = os.path.dirname(os.path.realpath(__file__))
kubeconfig = " --config=" + os.path.join(config_path, "node.kubeconfig")


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


def run_command(command):
    try:
        p = Popen(command, bufsize=0, shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)
        #p.wait()
        out = p.communicate()
        return out
    except Exception as e:
        logger.critical(e.message, extra={'locals': locals()}, extra_info=True)
        return e.message


def start_delivery(job_details):
    try:
        logger.debug("Retrieving namespace")
        name_space = job_details['name_space']
        oc_name = hashlib.sha224(name_space).hexdigest()
        logger.debug("Openshift project namespace is hashed from {0} to {1}, hash can be reproduced with sha224 tool"
                  .format(name_space, oc_name))
        notify_email = job_details['notify_email']

        #tag = job_details['tag']
        #depends_on = job_details['depends_on']

        logger.debug("Login to OpenShift server")
        command_login = "oc login https://OPENSHIFT_SERVER_IP:8443 -u test-admin -p test" + \
            kubeconfig + " --certificate-authority=" + config_path + "/ca.crt"
        out = run_command(command_login)
        logger.debug(out)

        logger.debug(" change project to the desired one")
        command_change_project = "oc project " + oc_name + kubeconfig
        out = run_command(command_change_project)
        logger.debug(out)

        logger.debug("start the delivery")
        command_start_build = "oc --namespace " + oc_name + \
            " start-build delivery" + kubeconfig
        out = run_command(command_start_build)
        logger.debug(out)

        build_details = out[0].split('"')[-1].rstrip()
        logger.debug(build_details)

        if build_details == "":
            logger.critical("build could not be started as OpenShift is not reachable")
            return 1

        logger.debug("Delivery started is " + build_details)

        status_command = "oc get --namespace " + oc_name + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1

        logger.debug("Checking the delivery status")
        while is_running >= 0:
            status = run_command(status_command)[0].rstrip()
            is_running = re.search("New|Pending|Running", status)
            logger.debug("current status: " + status)
            time.sleep(30)

        is_complete = run_command(status_command)[0].find('Complete')
        # checking logs for the build phase
        log_command = "oc logs --namespace " + oc_name + " build/" + \
            build_details + kubeconfig
        logs = run_command(log_command)
        logs = logs[0]

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            notify_build_failure(name_space, notify_email, logs)
            logger.debug(
                "Delivery is not successful putting it to failed build tube")
        else:
            bs.use('tracking')
            bs.put(json.dumps(job_details))
            bs.use("delivery_failed")

        return 0
    except Exception as e:
        logger.critical(e.message, exc_info=True, extra={'locals': locals()})
        return 1


def main():
    while True:
        try:
            logger.debug("listening to start_delivery tube")
            job = bs.reserve()
            job_details = json.loads(job.body)
            result = start_delivery(job_details)
            if result == 0:
                logger.debug("Delivery is successful deleting the job")
                job.delete()
            else:
                logger.debug("Job was not succesfull and returned to tube")
        except Exception as e:
            logger.critical(e.message, extra={'locals': locals()}, exc_info=True)

if __name__ == '__main__':
    main()
