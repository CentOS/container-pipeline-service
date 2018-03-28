#!/usr/bin/env python

from datetime import datetime
from time import sleep
import docker
import json
import logging
import os
import sys

OUTDIR = "/scanout"
IMAGE_NAME = os.environ.get("IMAGE_NAME")

# set up logging
logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Client connecting to Docker socket
client = docker.Client(base_url="unix:///var/run/docker.sock")

# Argument passed to script. Decides package manager to check for.
cli_arg = sys.argv[1]

# image UUID
UUID = client.inspect_image(IMAGE_NAME)["Id"].split(':')[-1]


def binary_does_not_exist(response):
    """
    Used to figure if the npm, pip, gem binary exists in the container image
    """
    if 'executable file not found in' in response or 'not found' in response \
            or 'no such file or directory' in response:
        return True
    return False


def split_by_newline(response):
    """
    Return a list of string split by newline character
    """
    return response.split("\n")


def remove_last_blank_character(response):
    """
    Last value of response could be ''. Remove that if that's the case
    """
    if response[-1] == '':
        response = response[:-1]
    return response


def list_of_outdated_packages(response):
    """
    Return a list containing outdated packages for a package manager
    """
    outdated_packages = []

    for _ in response:
        outdated_packages.append(_.split()[0])

    return outdated_packages


def pip_list_of_outdated_packages(response):
    """
    List of oudated packages for pip package manager
    """
    # pip returns a string output separated by '\n'
    response = split_by_newline(response)

    response = remove_last_blank_character(response)

    outdated_packages = list_of_outdated_packages(response)

    # if newer version of pip is being used inside the container under scan, a
    # DEPRECATION warning is raised by pip; we must ignore this.

    if "DEPRECATION:" in outdated_packages[0]:
        return outdated_packages[1:]

    return outdated_packages


def npm_list_of_outdated_packages(response):
    """
    List of oudated packages for npm package manager
    """
    # like pip, npm returns '\n' separated output but first line can be ignored
    response = split_by_newline(response)[1:]

    response = remove_last_blank_character(response)

    return list_of_outdated_packages(response)


def gem_list_of_outdated_packages(response):
    """
    List of oudated packages for gem package manager
    """
    # like pip, gem returns '\n' separated output
    response = split_by_newline(response)

    response = remove_last_blank_character(response)

    return list_of_outdated_packages(response)


def format_response(cli_arg, response):
    """
    Based on the CLI argument provided, check for the
    package updates related to the package manager
    """
    if cli_arg == 'pip':
        return pip_list_of_outdated_packages(response)
    elif cli_arg == "npm":
        return npm_list_of_outdated_packages(response)
    elif cli_arg == "gem":
        return gem_list_of_outdated_packages(response)


def template_json_data(scan_type):
    """
    Template data on top of which additional data that is provided by different
    functions is added
    """
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    json_out = {
        "Start Time": current_time,
        "Successful": False,
        "Scan Type": scan_type + "-updates",
        "UUID": UUID,
        "CVE Feed Last Updated": "NA",
        "Scanner": "Misc Package Updates",
        "Scan Results": {"{} package updates".format(cli_arg): []},
        "Summary": ""
    }
    return json_out


def create_container(client, image, ep, cmd):
    """
    Execute given cmd in container via client
    """
    response = ""
    try:
        # create the container
        container = client.create_container(
            image=image,
            entrypoint=ep,
            command=cmd
        )
        # start the container
        client.start(container=container.get("Id"))
        # pause for 10 seconds for package manager to collect data
        sleep(10)
        # get the logs from container
        response = client.logs(container=container.get("Id"))
    except Exception as e:
        logger.log(
            level=logging.ERROR,
            msg="{} failed in scanner: {}".format(cmd, e)
        )
    else:
        return response
    finally:
        client.remove_container(
            container=container.get("Id"), force=True, v=True)


json_out = template_json_data(cli_arg)
response = ""
try:
    # Check for pip updates
    if cli_arg == "pip":
        response = create_container(
            client, IMAGE_NAME,
            ep="/usr/bin/pip",
            cmd="list --outdated")

    # Check for rubygem updates
    elif cli_arg == "gem":
        response = create_container(
            client, IMAGE_NAME,
            ep="/usr/bin/gem",
            cmd="outdated")

    # Check for npm updates
    elif cli_arg == "npm":
        response = create_container(
            client, IMAGE_NAME,
            ep="/usr/bin/npm",
            cmd="outdated -g")

except Exception as e:
    logger.log(
        level=logging.ERROR,
        msg="Scanner failed: {}".format(e)
    )

finally:
    if not response or binary_does_not_exist(response):
        json_out["Scan Results"] = \
            "Could not find {} executable in the image".format(cli_arg)
        json_out["Successful"] = False
        json_out["Summary"] = "No updates for packages installed via {}. ".\
            format(cli_arg)
    else:
        json_out["Scan Results"]["{} package updates".format(cli_arg)] = \
            format_response(cli_arg, response)
        json_out["Finished Time"] = \
            datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        json_out["Successful"] = True
        json_out["Summary"] = "Possible updates for packages installed via " \
            "{}. ".format(cli_arg)


output_dir = os.path.join(OUTDIR, UUID)
os.makedirs(output_dir)

output_file_relative = "image_scan_results.json"

output_file_absoulte = os.path.join(output_dir, output_file_relative)

with open(output_file_absoulte, "w") as f:
    f.write(json.dumps(json_out, indent=4))
