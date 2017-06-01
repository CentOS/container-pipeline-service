#!/usr/bin/python
"""pipeline scanner class."""
import json
import logging
import os
import shutil
import subprocess

import docker
from Atomic import Atomic, mount
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.settings import SCANNERS_OUTPUT


class PipelineScanner(object):
    """pipeline-scanner atomic scanner handler."""

    def __init__(self):
        """Get atomic object for the image."""
        self.scanner_name = "pipeline-scanner"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/pipeline-scanner"
        self.mount_object = mount.Mount()

        # Add logger
        load_logger()
        self.logger = logging.getLogger('scan-worker')

        DOCKER_HOST = "127.0.0.1"
        DOCKER_PORT = "4243"
        try:
            # docker client connection to CentOS 7 system
            self.conn = docker.Client(base_url="tcp://{}:{}".format(
                DOCKER_HOST, DOCKER_PORT
            ))
        except Exception as e:
            self.logger.fatal(
                "Error connecting to Docker daemon. Error {}".format(e),
                exc_info=True)

    def mount_image(self):
        """Mount image on local file system."""
        # get the SHA ID of the image.

        self.mount_object.mountpoint = self.image_rootfs_path
        self.mount_object.image = self.image_id

        # mount the rootfs in read-write mode. else yum will fail
        self.mount_object.options = ["rw"]

        # configure options before mounting the image rootfs
        self.logger.info("Setting up system to mount image's rootfs")

        # create a directory /<image_id> where we'll mount image's rootfs
        try:
            os.makedirs(self.image_rootfs_path)
        except OSError as error:
            self.logger.warning(msg=str(error), exc_info=True)
            self.logger.info(
                "Unmounting and removing directory {}".format(
                    self.image_rootfs_path))
            try:
                self.mount_object.unmount()
            except Exception as e:
                self.logger.warning(
                    "Failed to unmount path= {} - Error: {}".format(
                        self.image_rootfs_path, str(e)),
                    exc_info=True)
            else:
                try:
                    shutil.rmtree(self.image_rootfs_path)
                except Exception as e:
                    self.logger.warning(
                        "Failed to remove= {} - Error: {}".format(
                            self.image_rootfs_path, str(e)),
                        exc_info=True
                    )
            # retry once more
            try:
                os.makedirs(self.image_rootfs_path)
            except OSError as error:
                self.logger.critical(str(error), exc_info=True)
                # fail! and return
                return False

        self.logger.info(
            "Mounting rootfs {} on {}".format(
                self.image_id, self.image_rootfs_path))
        self.mount_object.mount()
        self.logger.info("Successfully mounted image's rootfs")
        return True

    def unmount_image(self):
        """Unmount image using the Atomic mount object."""
        self.logger.info("Unmounting image's rootfs from {}".format(
            self.mount_object.mountpoint))
        # TODO: Error handling and logging
        self.mount_object.unmount()

    def remove_image(self):
        """
        Clear up the scanned image.

        Removes the mounted image rootfs path as well as
        removes the image using docker
        """
        try:
            shutil.rmtree(self.image_rootfs_path)
        except OSError as error:
            self.logger.warning(
                "Error removing image rootfs path. Error {}".format(
                    str(error)),
                exc_info=True
            )
        self.logger.info(
            "Removing the image {}".format(self.image_under_test))
        self.conn.remove_image(image=self.image_under_test, force=True)

    def scan(self, image_under_test):
        """Run the pipleline scanner."""
        self.image_under_test = image_under_test
        self.image_id = Atomic().get_input_id(image_under_test)
        self.image_rootfs_path = os.path.join("/", self.image_id)

        json_data = {}

        if not self.mount_image():
            return False, json_data

        cmd = [
            'atomic',
            'scan',
            "--scanner={}".format(self.scanner_name),
            "--rootfs={}".format(self.image_rootfs_path),
            "{}".format(self.image_id)
        ]

        self.logger.info("Executing atomic scan:  {}".format(" ".join(cmd)))
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        out, err = process.communicate()

        if out != "":
            # TODO: hacky and ugly. figure a better way
            # https://github.com/projectatomic/atomic/issues/577
            output_json_file = os.path.join(
                out.strip().split()[-1].split('.')[0],
                "_{}".format(self.image_rootfs_path.split('/')[1]),
                SCANNERS_OUTPUT[self.full_scanner_name][0]
            )
            self.logger.info("Result file: {}".format(output_json_file))

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
            else:
                self.logger.critical(
                    "No scan results found at {}".format(output_json_file))
                return False, json_data
        else:
            self.logger.warning(
                "Failed to get the results from atomic CLI. Error:{}".format(
                    err)
            )
            return False, json_data

        self.unmount_image()
        shutil.rmtree(self.image_rootfs_path, ignore_errors=True)
        self.logger.info(
            "Finished executing scanner: {}".format(self.scanner_name))
        return True, self.process_output(json_data)

    def process_output(self, json_data):
        """
        Process output based on its content.

        Process the output from the scanner, parse the json and
        add meaningful information based on validations
        """
        data = {}
        data["scanner_name"] = self.scanner_name
        if json_data["Scan Results"]["Package Updates"]:
            data["logs"] = json_data
            data["msg"] = "Container image requires update."
        else:
            data["logs"] = {}
            data["msg"] = "No updates required."
        return data
