#!/usr/bin/python
"""
Scanner Runner.

This module invokes all registered scanners and orchestrates the processing.
"""

import docker
import json
import logging
import os

from container_pipeline.lib import settings
from container_pipeline.lib.log import load_logger
from container_pipeline.scanners.container_capabilities import \
    ContainerCapabilities
from container_pipeline.scanners.misc_package_updates import \
    MiscPackageUpdates
from container_pipeline.scanners.pipeline_scanner import PipelineScanner
from container_pipeline.scanners.rpm_verify import ScannerRPMVerify
from container_pipeline.scanners.base import Scanner


class ScannerRunner(Scanner):
    """
    Scanner Handler orchestration.

    Scanner runner class handling basic operation and orchestration of
    multiple scanner handlers
    """

    def __init__(self, job):
        """Initialize runner."""
        # initializing logger
        load_logger()
        self.logger = logging.getLogger('scan-worker')
        self.docker_conn = self.docker_client()
        self.job = job

        # register all scanners
        self.scanners = [
            PipelineScanner,
            ScannerRPMVerify,
            MiscPackageUpdates,
            ContainerCapabilities
        ]

    def docker_client(self, host="127.0.0.1", port="4243"):
        """
        returns Docker client object on success else False on failure
        """
        try:
            conn = docker.Client(base_url="tcp://{}:{}".format(host, port))
        except Exception as e:
            self.logger.fatal(
                "Failed to connect to Docker daemon. {}".format(e),
                exc_info=True)
            return False
        else:
            return conn

    def remove_image(self, image):
        """
        Remove the image under test using docker client
        """
        self.logger.info("Removing image {}".format(image))
        self.docker_conn.remove_image(image=self.image, force=True)

    def pull_image(self, image):
        """
        Pull image under test on scanner host machine
        """
        self.logger.info("Pulling image {}".format(image))
        pull_data = self.docker_conn.pull(repository=image)

        if 'error' in pull_data:
            self.logger.fatal("Error pulling requested image {}: {}".format(
                image, pull_data
            ))
            return False

        self.logger.info("Pulled image {}".format(image))
        return True

    def export_scanners_status(self, status, status_file_path):
        """
        Export status of scanners execution for build in process.
        """
        try:
            fin = open(status_file_path, "w")
            json.dump(status, fin, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanners status on NFS share.")
            self.logger.critical(str(e))
        else:
            self.logger.info(
                "Wrote scanners status to file: {}".format(status_file_path))

    def export_scanner_result(self, data, result_file):
        """
        Export scanner logs in given directory.
        """
        try:
            fin = open(result_file, "w")
            json.dump(data, fin, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanner result file {}".format(result_file))
            self.logger.critical(str(e), exc_info=True)
            return None
        else:
            self.logger.info(
                "Exported scanner result file {}".format(result_file))
            return True

    def run_a_scanner(self, scanner_obj, image):
        """
        Run the given scanner on image.
        """
        # should receive the JSON data loaded
        data = scanner_obj.run(image)

        self.logger.info("Finished running {} scanner.".format(
            scanner_obj.scanner))

        return data

    def scan(self):
        """
        Run the listed atomic scanners on image under test.

        # FIXME: at the moment this menthod is returning the results of
        multiple scanners in one json and sends over the bus
        """
        self.logger.info("Received scanning job : {}".format(self.job))

        image = self.job.get("image_under_test")

        self.logger.info("Image under test for scanning :{}".format(image))
        # copy the job info into scanners data,
        # as we are going to add logs and msg
        scanners_data = self.job
        scanners_data["msg"] = {}
        scanners_data["logs_URL"] = {}
        scanners_data["logs_file_path"] = {}

        # pull the image first, if failed move on to start_delivery
        if not self.pull_image(image):
            self.logger.info(
                "Image pulled failed, moving job to delivery phase.")
            scanners_data["action"] = "start_delivery"
            return False, scanners_data

        # run the multiple scanners on image under test
        for scanner in self.scanners:
            # create object for the respective scanner class
            scanner_obj = scanner()
            # execute atomic scan and grab the results
            result = self.run_a_scanner(scanner_obj, image)

            # each scanner invoker class defines the output result file
            result_file = os.path.join(
                self.job["logs_dir"], scanner_obj.result_file)

            # for only the cases where export/write operation could fail
            if not self.export_scanner_result(result, result_file):
                continue

            # keep the message
            scanners_data["msg"][result["scanner"]] = result["msg"]

            # pass the logs filepath via beanstalk tube
            # TODO: change the respective key from logs ==> logs_URL while
            # accessing this
            # scanner results logs URL
            scanners_data["logs_URL"][result["scanner"]] = result_file.replace(
                settings.LOGS_DIR,
                settings.LOGS_URL_BASE)

            # put the logs file name as well here in data
            scanners_data["logs_file_path"][result["scanner"]] = result_file

        # TODO: Check here if at least one scanner ran successfully
        self.logger.info("Finished executing all scanners.")

        # keep notify_user action in data, even if we are deleting the job,
        # since whenever we will read the response, we should be able to see
        # action
        scanners_data["action"] = "notify_user"

        status_file_path = os.path.join(
            self.job["logs_dir"],
            settings.SCANNERS_STATUS_FILE)

        # We export the scanners_status on NFS
        self.export_scanners_status(scanners_data, status_file_path)

        # clean up the system
        self.clean_up(image)

        return True, scanners_data

    def clean_up(self, image):
        """
        Clean up the system post scan
        """
        # after all scanners are ran, remove the image
        self.logger.info("Removing the image: {}".format(image))
        self.docker_conn.remove_image(image=image, force=True)
