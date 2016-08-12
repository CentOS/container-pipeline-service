#!/usr/bin/python

import beanstalkc
import json
import logging
import os
import subprocess
import sys

logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)


def write_dockerfile(dockerfile):
    if os.path.isdir("/tmp/scan"):
        logger.log(level=logging.INFO, msg="/tmp/scan directory already exists")
    elif os.path.isfile("/tmp/scan"):
        os.remove("/tmp/scan")
        os.makedirs("/tmp/scan")
    else:
        os.makedirs("/tmp/scan")

    with open("/tmp/scan/dockerfile", "w") as f:
        f.write(dockerfile)


def lint_job_data(job_data):
    logger.log(level=logging.INFO, msg="Received job data from tube")
    logger.log(level=logging.INFO, msg="Job data: %s" % job_data)

    namespace = job_data.get('name_space')

    dockerfile = job_data.get("dockerfile")

    logger.log(level=logging.INFO,
               msg="Writing Dockerfile to /tmp/scan/dockerfile")
    write_dockerfile(dockerfile)

    logger.log(level=logging.INFO, msg="Running Dockerfile Lint check")
    out, err = subprocess.Popen(
        ["docker",
         "run",
         "--rm",
         "-v",
         "/tmp/scan:/root/scan:Z",
         "registry.centos.org/dharmit/dockerfile-lint"],
        stdout=subprocess.PIPE
    ).communicate()
    logger.log(level=logging.INFO, msg="Dockerfile Lint check done")

    response = {
        "logs": out,
        "action": "notify_user",
        "namespace": namespace
    }

    bs.use("master_tube")
    jid = bs.put(json.dumps(response))
    logger.log(
        level=logging.INFO,
        msg="Put job on 'master_tube' tube with id: %d" % jid
    )


bs = beanstalkc.Connection(host="openshift")
bs.watch("start_lint")

while True:
    try:
        job = bs.reserve()
        job_data = json.loads(job.body)
        lint_job_data(job_data)
        job.delete()
    except Exception as e:
        logger.log(level=logging.FATAL, msg=e.message)
