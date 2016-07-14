#!/usr/bin/python

import beanstalkc
import docker
import json
import logging
import os
import subprocess
import sys

from Atomic import Atomic, mount

# CENTOS7 = "dev-32-94.lon1.centos.org"
# DOCKER_PORT = "4243"

logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

# set blank values so that they can be used later to clean environment

image_id = ""
image_rootfs_path = ""

try:
    # docker client connection to CentOS 7 system
    # conn = docker.Client(base_url="tcp://%s:%s" % (
    #     CENTOS7, DOCKER_PORT
    # ))
    # conn.ping()
    # logger.log(level=logging.INFO, msg="Connected to remote docker host %s:%s" %
    #            (CENTOS7, DOCKER_PORT))
    conn = docker.Client(base_url="unix:///var/run/docker.sock")
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

    # Receive and send `name_space` key-value as is
    namespace = job_data.get('name_space')

    image_full_name = job_data.get('name').split(":")[0] + ":" + \
        job_data.get("tag")

    logger.log(level=logging.INFO, msg="Pulling image %s" % image_full_name)
    pull_data = conn.pull(
        repository=image_full_name
    )

    if 'error' in pull_data:
        logger.log(level=logging.FATAL, msg="Couldn't pull requested image")
        logger.log(level=logging.FATAL, msg=pull_data)
        raise

    # logger.log(level=logging.INFO,
    #            msg="Creating container for image %s" % image_full_name)

    # container = conn.create_container(image=image_full_name,
    #                                      command="yum -q check-update")

    atomic_object = Atomic()
    # get the SHA ID of the image.
    image_id = atomic_object.get_input_id(image_full_name)
    image_rootfs_path = os.path.join("/", image_id)

    # create a directory /<image_id> where we'll mount image's rootfs
    os.makedirs(image_rootfs_path)

    # configure options before mounting the image rootfs
    logger.log(level=logging.INFO,
               msg="Setting up system to mount image's rootfs")
    mount_object = mount.Mount()
    mount_object.mountpoint = image_rootfs_path
    mount_object.image = image_id
    # mount the rootfs in read-write mode. else yum will fail
    mount_object.options = ["rw"]

    logger.log(level=logging.INFO,
               msg="Mounting rootfs %s on %s" % (image_id, image_rootfs_path))

    mount_object.mount()

    logger.log(level=logging.INFO,
               msg="Successfully mounted image's rootfs")

    cmd = "atomic scan --scanner=%s --rootfs=%s %s" % \
        ("pipeline-scanner", image_rootfs_path, image_id)

    logger.log(level=logging.INFO,
               msg="Executing atomic scan: %s" % cmd)

    process = subprocess.Popen([
        'atomic',
        'scan',
        "--scanner=pipeline-scanner",
        "--rootfs=%s" % image_rootfs_path,
        "%s" % image_id
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    out, err = process.communicate()

    # logger.log(level=logging.INFO,
    #            msg="Created container with ID: %s" % container.get('Id'))

    # conn.start(container=container.get('Id'))

    # logger.log(level=logging.INFO,
    #            msg="Started container with ID: %s" % container.get('Id'))

    # time.sleep(10)
    # logs = conn.logs(container=container.get('Id'))

    # logger.log(level=logging.INFO, msg="Stopping test container")
    # conn.stop(container=container.get('Id'))

    # logger.log(level=logging.INFO, msg="Removing the test container")
    # conn.remove_container(container=container.get('Id'), force=True)

    if out != "":
        # TODO: hacky and ugly. figure a better way
        output_json_file = os.path.join(
            out.strip().split()[-1].split('.')[0],
            "_%s" % image_rootfs_path.split('/')[1],
            "image_scan_results.json"
        )

        if os.path.exists(output_json_file):
            json_data = json.loads(open(output_json_file).read())
        else:
            logger.log(level=logging.FATAL,
                       msg="No scan results found at %s" % output_json_file)
            raise
    else:
        logs = ""

    logger.log(level=logging.INFO,
               msg="Unmounting image's rootfs from %s" % image_rootfs_path)

    mount_object.unmount()

    os.rmdir(image_rootfs_path)

    logger.log(level=logging.INFO, msg="Removing the image %s" % image_full_name)
    conn.remove_image(image=image_full_name, force=True)

    logger.log(level=logging.INFO, msg="Finished test...")

    # if msg != "" and logs != "":
    if json_data != None:
        d = {
            "image": image_full_name,
            "msg": "Container image requires update",
            "logs": json.dumps(json_data),
            "action": "start_delivery",
            "name_space": namespace
        }
    else:
        d = {
            "image": image_full_name,
            "msg": "No updates required",
            "logs": "",
            "action": "start_delivery",
            "name_space": namespace
        }
    bs.use("master_tube")
    jid = bs.put(json.dumps(d))
    logger.log(
        level=logging.INFO,
        msg="Put job on master tube with id: %d" % jid
    )

bs = beanstalkc.Connection(host="localhost")
bs.watch("start_test")

while True:
    try:
        job = bs.reserve()
        job_data = json.loads(job.body)
        test_job_data(job_data)
        job.delete()
    except Exception as e:
        logger.log(level=logging.FATAL, msg=e.message)
