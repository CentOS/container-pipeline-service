#!/usr/bin/python

import constants
import docker
import json
import logging
import os
import shutil
import subprocess
import config
import hashlib

from Atomic import Atomic, mount
from scanner import Scanner

from container_pipeline.utils import Build, get_job_name
from container_pipeline.lib.log import load_logger
from container_pipeline.workers.base import BaseWorker

class PipelineScanner(object):
    """
    pipeline-scanner atomic scanner handler
    """

    def __init__(self):
        self.scanner_name = "pipeline-scanner"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/pipeline-scanner"
        self.atomic_object = Atomic()
        self.mount_object = mount.Mount()

    def mount_image(self):
        """
        Mount image on local file system
        """
        # get the SHA ID of the image.

        self.mount_object.mountpoint = self.image_rootfs_path
        self.mount_object.image = self.image_id

        # mount the rootfs in read-write mode. else yum will fail
        self.mount_object.options = ["rw"]

        # configure options before mounting the image rootfs
        logger.info("Setting up system to mount image's rootfs")

        # create a directory /<image_id> where we'll mount image's rootfs
        try:
            os.makedirs(self.image_rootfs_path)
        except OSError as error:
            logger.warning(msg=str(error), exc_info=True)
            logger.info(
                "Unmounting and removing directory %s "
                % self.image_rootfs_path)
            try:
                self.mount_object.unmount()
            except Exception as e:
                logger.warning(
                    "Failed to unmount path= %s - Error: %s" % (
                        self.image_rootfs_path, str(e)),
                    exc_info=True)
            else:
                try:
                    shutil.rmtree(self.image_rootfs_path)
                except Exception as e:
                    logger.warning(
                        "Failed to remove= %s - Error: %s" % (
                            self.image_rootfs_path, str(e)),
                        exc_info=True
                    )
            # retry once more
            try:
                os.makedirs(self.image_rootfs_path)
            except OSError as error:
                logger.fatal(str(error), exc_info=True)
                # fail! and return
                return False

        logger.info(
            "Mounting rootfs %s on %s" % (
                self.image_id, self.image_rootfs_path))
        self.mount_object.mount()
        logger.info("Successfully mounted image's rootfs")
        return True

    def unmount_image(self):
        """
        Unmount image using the Atomic mount object
        """
        logger.info("Unmounting image's rootfs from %s"
                    % self.mount_object.mountpoint)
        # TODO: Error handling and logging
        self.mount_object.unmount()

    def remove_image(self):
        """
        Removes the mounted image rootfs path as well as
        removes the image using docker
        """
        try:
            shutil.rmtree(self.image_rootfs_path)
        except OSError as error:
            logger.warning(
                "Error removing image rootfs path. %s" % str(error),
                exc_info=True
            )
        logger.info(
            "Removing the image %s" % self.image_under_test)
        conn.remove_image(image=self.image_under_test, force=True)

    def scan(self, image_under_test):
        """
        Run the scanner
        """
        self.image_under_test = image_under_test
        self.image_id = self.atomic_object.get_input_id(image_under_test)
        self.image_rootfs_path = os.path.join("/", self.image_id)

        json_data = {}

        if not self.mount_image():
            return False, json_data

        cmd = [
            'atomic',
            'scan',
            "--scanner=%s" % self.scanner_name,
            "--rootfs=%s" % self.image_rootfs_path,
            "%s" % self.image_id
        ]

        logger.info("Executing atomic scan:  %s" % " ".join(cmd))
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
                "_%s" % self.image_rootfs_path.split('/')[1],
                SCANNERS_OUTPUT[self.full_scanner_name][0]
            )
            logger.info("Result file: %s" % output_json_file)

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
            else:
                logger.fatal(
                    "No scan results found at %s" % output_json_file)
                return False, json_data
        else:
            logger.warning(
                "Failed to get the results from atomic CLI. Error:%s" % err
            )
            return False, json_data

        self.unmount_image()
        shutil.rmtree(self.image_rootfs_path, ignore_errors=True)
        logger.info(
            "Finished executing scanner: %s" % self.scanner_name)
        return True, self.process_output(json_data)

    def process_output(self, json_data):
        """
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
