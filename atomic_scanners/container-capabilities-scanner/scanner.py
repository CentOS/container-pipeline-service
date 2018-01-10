#!/usr/bin/env python

# import docker
import json
import logging
import os
import subprocess
import sys

from Atomic import run
from datetime import datetime

INDIR = "/scanin"
OUTDIR = "/scanout"
IMAGE_NAME = os.environ.get("IMAGE_NAME")

# object of atomic run
run_object = run.Run()
run_object.image = IMAGE_NAME

# client = docker.Client(base_url="unix:///var/run/docker.sock")

# set up logging
logger = logging.getLogger("container-capabilities-scanner")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

# image UUID
UUID = run_object.get_input_id(IMAGE_NAME)


class RunLabelException(Exception):
    """
    This is a custom exception which should be raised when RUN label for
    container image under scan is empty
    """

    def __init__(self, message):
        super(RunLabelException, self).__init__(message)


def check_image_for_run_label(image):
    """
    If image under scan doesn't have a RUN label, raise RunLabelException
    """
    run_label = run_object.get_label("RUN")

    if run_label == "":
        raise RunLabelException(
            "Dockerfile for the image doesn't have RUN label.")
    return run_label


def split_by_newline(response):
    """
    Return a list of string split by newline character
    """
    return response.split("\n")


def template_json_data():
    """
    Template data on top of which additional data that is provided by different
    functions is added
    """
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    json_out = {
        "Start Time": current_time,
        "Successful": "",
        "Scan Type": "check-capabilities",
        "UUID": UUID,
        "CVE Feed Last Updated": "NA",
        "Scanner": "Container Capabilities Scanner",
        "Scan Results": {"Container capabilities": None},
        # "Docker run command": "docker run -d {} tailf /dev/null".format(
        #     IMAGE_NAME),
        "Reference documentation": "http://www.projectatomic.io/blog/2016/01/"
        "how-to-run-a-more-secure-non-root-user-container/",
        "Summary": ""
    }
    return json_out


json_out = template_json_data()

try:
    # Check if the image under scan has a RUN label
    # More info on Dockerfile labels:
    # https://docs.docker.com/engine/reference/builder/#/label
    run_label = check_image_for_run_label(image=IMAGE_NAME)

    # run_object.check_args(run_label)

    out, err = subprocess.Popen(
        [
            "python",
            "run_scanner.py"
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE
    ).communicate()

    if out is not None:
        json_out["Scan Results"]["Container capabilities"] = out

        if out == "":
            json_out["Summary"] = "No additional capabilities found."
        else:
            json_out["Summary"] = \
                "Container image has few additional capabilities."
    else:
        json_out["Scan Results"]["Container capabilities"] = \
            "This container image doesn't have any special capabilities"
        json_out["Summary"] = "No additional capabilities found."

    json_out["Successful"] = "true"

except RunLabelException as e:
    json_out["Scan Results"]["Container capabilities"] = e.message
    json_out["Successful"] = "false"
    json_out["Summary"] = "Dockerfile for the image doesn't have RUN label."
except Exception as e:
    logger.log(
        level=logging.ERROR,
        msg="Scanner failed: {}".format(e)
    )
    json_out["Summary"] = "Scanner failed."
finally:
    json_out["Finished Time"] = \
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')

output_dir = os.path.join(OUTDIR, UUID)
os.makedirs(output_dir)

output_file_relative = "container_capabilities_scanner_results.json"

output_file_absoulte = os.path.join(output_dir, output_file_relative)

with open(output_file_absoulte, "w") as f:
    f.write(json.dumps(json_out, indent=4))
