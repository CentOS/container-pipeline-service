#!/usr/bin/python

import beanstalkc
import json
import logging
import os
import subprocess
import sys

from constants import LINTER_IMAGE

logger = logging.getLogger("cccp-linter")
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

    with open("/tmp/scan/Dockerfile", "w") as f:
        f.write(dockerfile)


def lint_job_data(job_data):
    logger.log(level=logging.INFO, msg="Received job data from tube")
    logger.log(level=logging.INFO, msg="Job data: %s" % job_data)

    dockerfile = job_data.get("dockerfile")

    logger.log(level=logging.INFO,
               msg="Writing Dockerfile to /tmp/scan/Dockerfile")
    write_dockerfile(dockerfile)

    logger.log(level=logging.INFO, msg="Running Dockerfile Lint check")
    out, err = subprocess.Popen(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            "/tmp/scan:/root/scan:Z",
            LINTER_IMAGE
        ],
        stdout=subprocess.PIPE
    ).communicate()

    if err is None:
        logger.log(level=logging.INFO, msg="Dockerfile Lint check done")
        response = {
            "logs": out,
            "linter_results": True,
            "action": "notify_user",
            "namespace": job_data.get('namespace'),
            "notify_email": job_data.get("notify_email"),
            "job_name": job_data.get("job_name"),
            "msg": None
        }

    else:
        logger.log(level=logging.ERROR, msg="Dockerfile Lint check failed")
        response = {
            "linter_results": True,
            "action": "notify_user",
            "namespace": job_data.get('namespace'),
            "notify_email": job_data.get("notify_email"),
            "job_name": job_data.get("job_name"),
            "msg": err
        }

    bs.use("master_tube")
    jid = bs.put(json.dumps(response))
    logger.log(
        level=logging.INFO,
        msg="Put job on 'master_tube' tube with id: %d" % jid
    )


bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("start_linter")

while True:
    try:
        job = bs.reserve()
        job_data = json.loads(job.body)
        lint_job_data(job_data)
        job.delete()
    except Exception as e:
        logger.log(level=logging.FATAL, msg=e.message)
