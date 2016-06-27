#!/usr/bin/python

import beanstalkc
import docker
import json
import logging
import sys
import time

CENTOS7 = "dev-32-94.lon1.centos.org"
DOCKER_PORT = "4243"

logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

try:
    # docker client connection to CentOS 7 system
    conn_c7 = docker.Client(base_url="tcp://%s:%s" % (
        CENTOS7, DOCKER_PORT
    ))
    conn_c7.ping()
    logger.log(level=logging.INFO, msg="Connected to remote docker host %s:%s" %
               (CENTOS7, DOCKER_PORT))
except Exception as e:
    logger.log(level=logging.FATAL, msg="Error connecting to Docker daemon.")


def split_logs_to_packages(list_logs):
    package_list = []

    for i in list_logs:
        if i == "" or i.startswith("Repodata"):
            continue
        i_split = i.split(" ", 1)
        package_list.append(i_split[0])

    return package_list


def test_job_data(job_data):
    msg = ""
    logs = ""
    logger.log(level=logging.INFO, msg="Received job data from tube")
    logger.log(level=logging.INFO, msg="Job data: %s" % job_data)

    # if job_data.get("tag") != None:
    #     image_full_name = job_data.get("name") + ":" + \
    #         job_data.get("image_tag")
    # else:
    #     image_full_name = job_data.get("name")

    image_full_name = job_data.get('name').split(":")[0] + ":" + \
        job_data.get("tag")

    logger.log(level=logging.INFO, msg="Pulling image %s" % image_full_name)
    pull_data = conn_c7.pull(
        repository=image_full_name
    )

    if 'error' in pull_data:
        logger.log(level=logging.FATAL, msg="Couldn't pull requested image")
        logger.log(level=logging.FATAL, msg=pull_data)
        sys.exit(1)

    logger.log(level=logging.INFO,
               msg="Creating container for image %s" % image_full_name)

    container = conn_c7.create_container(image=image_full_name,
                                         command="yum -q check-update")
    logger.log(level=logging.INFO,
               msg="Created container with ID: %s" % container.get('Id'))

    conn_c7.start(container=container.get('Id'))

    logger.log(level=logging.INFO,
               msg="Started container with ID: %s" % container.get('Id'))

    time.sleep(10)
    logs = conn_c7.logs(container=container.get('Id'))
    if logs != "":
        list_logs = logs.split("\n")
        package_list = split_logs_to_packages(list_logs)
        msg = "Image has package updates. Recommend updating the image"
        logger.log(level=logging.WARN, msg=msg)
        logger.log(level=logging.INFO, msg=str(package_list))

    logger.log(level=logging.INFO, msg="Stopping test container")
    conn_c7.stop(container=container.get('Id'))

    logger.log(level=logging.INFO, msg="Removing the test container")
    conn_c7.remove_container(container=container.get('Id'), force=True)

    logger.log(level=logging.INFO, msg="Removing the image %s" % image_full_name)
    conn_c7.remove_image(image=image_full_name, force=True)

    logger.log(level=logging.INFO, msg="Finished test...")

    if msg != "" and logs != "":
        d = {"image": image_full_name, "msg": msg, "logs": package_list}
    else:
        d = {"image": image_full_name, "msg": "No updates required", "logs": ""}
    bs.use("start_deliver")
    jid = bs.put(json.dumps(d))
    logger.log(
        level=logging.INFO,
        msg="Put job on 'start_deliver' tube with id: %d" % jid
    )

bs = beanstalkc.Connection(host="openshift")
bs.watch("start_test")

while True:
    try:
        job = bs.reserve()
        job_data = json.loads(job.body)
        test_job_data(job_data)
        job.delete()
    except Exception as e:
        logger.log(level=logging.FATAL, msg=e.message)
