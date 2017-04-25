#!/usr/bin/env python

import beanstalkc
import hashlib
import json
from subprocess import Popen
from subprocess import PIPE
import re
import time
import logging
import os
import config
from lib import Build


bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("start_delivery")
bs.use("delivery_failed")

config.load_logger()
logger = logging.getLogger("delivery-worker")

config_path = os.path.dirname(os.path.realpath(__file__))
kubeconfig = " --config=" + os.path.join(config_path, "node.kubeconfig")


def notify_build_failure(job_details, logs):
    """
    Notify build failure via notification module to user
    """
    # other info like, namespace, notify_email, TEST_TAG etc are there
    job_details["build_status"] = False
    job_details["logs"] = logs
    job_details["action"] = "notify_user"
    bs.use('master_tube')

    bs.put(json.dumps(job_details))


def run_command(command):
    try:
        p = Popen(command, bufsize=0, shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)
        # p.wait()
        out = p.communicate()
        return out
    except Exception as e:
        logger.critical(e.message, extra={'locals': locals()}, extra_info=True)
        return e.message


def start_delivery(job_details):
    try:
        logger.debug("Retrieving namespace")
        namespace = job_details['namespace']
        oc_name = hashlib.sha224(namespace).hexdigest()
        logger.debug("Openshift project namespace is hashed from {0} to {1}, hash can be reproduced with sha224 tool"
                     .format(namespace, oc_name))
        notify_email = job_details['notify_email']

        # tag = job_details['tag']
        # depends_on = job_details['depends_on']

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
            logger.critical(
                "build could not be started as OpenShift is not reachable")
            return 1

        logger.debug("Delivery started is " + build_details)

        status_command = "oc get --namespace " + oc_name + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1
        empty_retry = 10

        logger.debug("Checking the delivery status")
        while is_running >= 0:
            status = run_command(status_command)[0].rstrip()
            if status:
                is_running = re.search("New|Pending|Running", status)
                logger.debug("current status: " + status)
            elif empty_retry > 0:
                logger.debug("Failed to fetch status, retries left " + str(empty_retry))
                empty_retry -= 1
                is_running = 1
            else:
                logger.debug("Failed to fetch build status multiple times, assuming failure.")
                is_running = 0
            time.sleep(30)

        is_complete = run_command(status_command)[0].find('Complete')
        # checking logs for the build phase
        log_command = "oc logs --namespace " + oc_name + " build/" + \
            build_details + kubeconfig
        logs = run_command(log_command)
        logs = logs[0]

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            notify_build_failure(job_details, logs)
            logger.debug(
                "Delivery is not successful putting it to failed build tube")
        else:
            bs.use('tracking')
            bs.put(json.dumps(job_details))
            bs.use("delivery_failed")
            logger.debug("Build is successfull going for next job")

        delete_pod_command = "oc delete pods " + build_details + \
            "-build --namespace " + oc_name + " " + kubeconfig
        is_deleted = run_command(delete_pod_command)[0].rstrip()
        logger.debug("pods deleted status " + is_deleted)

        return 0
    except Exception as e:
        logger.critical(e.message, exc_info=True, extra={'locals': locals()})
        return 1


def main():
    logger.info('Starting delivery worker')
    while True:
        try:
            job = bs.reserve()
            job_details = json.loads(job.body)
            logger.debug('Got job: %s' % job_details)
            result = start_delivery(job_details)
            if result == 0:
                logger.info("Delivery is successful deleting the job")
                # Mark container image build as complete
                Build(job_details['namespace']).complete()
                logger.info('Marked build: %s as complete'
                            % job_details['namespace'])
                job.delete()
            else:
                logger.info("Job was not succesful and returned to tube")
        except Exception as e:
            logger.critical(e.message, extra={
                            'locals': locals()}, exc_info=True)

if __name__ == '__main__':
    main()
