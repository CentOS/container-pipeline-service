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
from lib import Build, get_job_name


bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("start_build")
bs.use("failed_build")

config.load_logger()
logger = logging.getLogger("build-worker")


config_path = os.path.dirname(os.path.realpath(__file__))
kubeconfig = " --config=" + os.path.join(config_path, "node.kubeconfig")

DELAY = 30


def run_command(command):
    logger.debug("Running command: " + command)
    try:
        p = Popen(command, bufsize=0, shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)
        # p.wait()
        out, err = p.communicate()
        return out
    except Exception as e:
        logger.critical(e.message, extra={'locals': locals()}, exc_info=True)
        return e.message


def notify_build_failure(namespace, notify_email, build_logs_file, project,
                         jobid, test_tag):
    msg_details = {}
    msg_details['action'] = 'notify_user'
    msg_details['namespace'] = namespace
    msg_details['build_status'] = False
    msg_details['notify_email'] = notify_email
    msg_details['build_logs_file'] = build_logs_file
    msg_details['project_name'] = project
    msg_details['job_name'] = jobid
    msg_details['TEST_TAG'] = test_tag
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
        logger.critical("Failed writing logs to %s" % destination)
        logger.critical(str(e))


def start_build(job_details):
    try:
        logger.debug("Retrieving namespace")
        appid = job_details['appid']
        jobid = job_details['jobid']
        desired_tag = job_details['desired_tag']
        namespace = get_job_name(job_details)
        oc_name = hashlib.sha224(namespace).hexdigest()
        logger.debug(
            "Openshift project namespace is hashed from {0} to {1}, hash can"
            " be reproduced with sha224 tool be reproduced  with sha224 tool"
            .format(namespace, oc_name)
        )
        # depends_on = job_details['depends_on']
        notify_email = job_details['notify_email']
        # This will be a mounted directory
        build_logs_file = os.path.join(
            job_details["logs_dir"],
            "build_logs.txt"
        )
        debug_logs_file = os.path.join(
            job_details['logs_dir'],
            config.SERVICE_LOGFILE
        )

        # Run dfh.clean() to clean log files if no error is encountered in
        # post delivering build report mails to user
        dfh = config.DynamicFileHandler(logger, debug_logs_file)

        logger.debug("Login to OpenShift server")
        command_login = "oc login https://OPENSHIFT_SERVER_IP:8443 -u" \
                        " test-admin -p test" + kubeconfig + \
                        " --certificate-authority=" + config_path + "/ca.crt"
        out = run_command(command_login)
        logger.debug(out)

        logger.debug(" change project to the desired one")
        command_change_project = "oc project " + namespace + kubeconfig
        out = run_command(command_change_project)
        logger.debug(out)

        logger.debug("start the build")
        command_start_build = "oc --namespace " + oc_name + \
            " start-build build" + kubeconfig
        out = run_command(command_start_build)
        logger.debug(out)

        # mark container image build as running
        # This will be mark as complete on delivery complete
        Build(namespace).start()

        build_details = out.split('"')[-1].rstrip()
        logger.debug(build_details)

        if build_details == "":
            logger.critical(
                "build could not be started as OpenShift is not reachable"
            )
            return 1

        logger.debug("build started is " + build_details)

        status_command = "oc get --namespace " + oc_name + " build/" + \
            build_details + kubeconfig + "|grep -v STATUS"
        is_running = 1
        empty_retry = 10

        logger.debug("Checking the build status")
        while is_running >= 0:
            status = run_command(status_command).rstrip()
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
            time.sleep(DELAY)

        # checking logs for the build phase
        log_command = "oc logs --namespace " + oc_name + " build/" + \
            build_details + kubeconfig
        try:
            logs = run_command(log_command)
        except Exception as e:
            logger.critical(e.message)
            logs = "Could not retrieve build logs."
            logger.critical(logs)
        else:
            logger.info("Writing build logs to NFS share..")
        finally:
            # Export logs on disk in either case
            export_build_logs(logs, build_logs_file)

        is_complete = run_command(status_command).find('Complete')

        if is_complete < 0:
            bs.put(json.dumps(job_details))
            logger.info(
                "Build is not successful putting it to failed build tube")
            project = appid + "/" + jobid + ":" + desired_tag
            notify_build_failure(
                namespace, notify_email, build_logs_file,
                project, jobid, job_details["TEST_TAG"])
        else:
            bs.use("master_tube")
            job_details["action"] = "start_test"
            job_details["namespace"] = namespace
            bs.put(json.dumps(job_details))
            logger.debug("Build is successful going for next job")

        return 0
    except Exception as e:
        logger.critical(e.message, extra={'locals': locals()}, exc_info=True)
        return 1
    finally:
        if 'dfh' in locals():
            dfh.remove()


def main():
    logger.info('Starting build worker')
    while True:
        parent_build_running = False
        got_job = False
        try:
            current_jobs_in_tube = bs.stats_tube(
                'start_build')['current-jobs-ready']
            if current_jobs_in_tube > 0:
                job = bs.reserve()
                got_job = True
                job_details = json.loads(job.body)
                logger.info('Got job: %s' % job_details)
                parents = job_details.get('depends_on', '').split(',')
                parents_in_build = []
                for parent in parents:
                    is_build_running = Build(parent).is_running()
                    if is_build_running:
                        parents_in_build.append(parent)
                    parent_build_running = parent_build_running or \
                        is_build_running

                if parent_build_running:
                    logger.info('Parents in build: %s, pushing job: %s back '
                                'to queue' % (parents_in_build, job_details))
                    bs.use('master_tube')
                    bs.put(json.dumps(job_details))
                    bs.use('failed_build')
                else:
                    logger.info('Starting build for job: %s' % job_details)
                    result = start_build(job_details)
            else:
                logger.info("No job found to process looping again")
                time.sleep(DELAY)
        except Exception as e:
            logger.critical(
                e.message,
                extra={'locals': locals()},
                exc_info=True
            )
            time.sleep(DELAY)
        finally:
            if got_job:
                job.delete()
                logger.info("Deleting the job after build worker loop")

if __name__ == '__main__':
    main()
