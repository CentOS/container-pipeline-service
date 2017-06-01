#!/usr/bin/python
"""Scanner Runner."""
import json
import logging
import os

import container_pipeline.lib.settings as constants
import docker
from container_pipeline.lib.log import load_logger
from container_pipeline.workers.scanners.container_capabilities import \
    ContainerCapabilities
from container_pipeline.workers.scanners.misc_package_updates import \
    MiscPackageUpdates
from container_pipeline.workers.scanners.pipeline import PipelineScanner
from container_pipeline.workers.scanners.rpm_verify import ScannerRPMVerify


class ScannerRunner(object):
    """
    Scanner Handler orchastration.

    Scanner runner class handling basic operation and orchestration of
    multiple scanner handlers
    """

    def __init__(self, job_info):
        """Initialize runner."""
        self.job_info = job_info

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

        # initializing logger
        load_logger()
        self.logger = logging.getLogger('scan-worker')

        # Receive and send `namespace` key-value as is
        self.job_namespace = job_info.get('namespace')
        self.scanners = {
            "registry.centos.org/pipeline-images/pipeline-scanner":
            PipelineScanner,
            "registry.centos.org/pipeline-images/scanner-rpm-verify":
            ScannerRPMVerify,
            "registry.centos.org/pipeline-images/misc-package-updates":
            MiscPackageUpdates,
            "registry.centos.org/pipeline-images/"
            "container-capabilities-scanner":
            ContainerCapabilities
        }

    def pull_image_under_test(self, image_under_test):
        """Pull image under test on test run host."""
        self.logger.info("Pulling image {}".format(image_under_test))
        pull_data = self.conn.pull(
            repository=image_under_test
        )

        if 'error' in pull_data:
            self.logger.fatal("Error pulling requested image {}: {}".format(
                image_under_test, pull_data
            ))
            return False
        self.logger.info("Image is pulled {}".format(image_under_test))
        return True

    def run_a_scanner(self, scanner, image_under_test):
        """Run the given scanner on image_under_test."""
        json_data = {}
        # create object for the respective scanner class
        scanner_obj = self.scanners.get(scanner)()
        # should receive the JSON data loaded
        status, json_data = scanner_obj.scan(image_under_test)

        if not status:
            self.logger.warning("Failed to run the scanner {}".format(scanner))
        else:
            self.logger.info("Finished running {} scanner.".format(scanner))

        # if scanner failed to run, this will return {}, do check at receiver
        # end
        return json_data

    def export_scanners_status(self, status, status_file_path):
        """Export status of scanners execution for build in process."""
        try:
            fin = open(status_file_path, "w")
            json.dump(status, fin)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanners status on NFS share.")
            self.logger.critical(str(e))
        else:
            self.logger.info(
                "Wrote scanners status to file: {}".format(status_file_path))

    def export_scanner_logs(self, scanner, data):
        """Export scanner logs in given directory."""
        logs_file_path = os.path.join(
            self.job_info["logs_dir"],
            constants.SCANNERS_RESULTFILE[scanner][0])
        self.logger.info(
            "Scanner={} result log file:{}".format(scanner, logs_file_path)
        )
        try:
            fin = open(logs_file_path, "w")
            json.dump(data, fin, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.critical(
                "Failed to write scanner={} logs on NFS share.".format(
                    scanner))
            self.logger.critical(str(e), exc_info=True)
        else:
            self.logger.info(
                "Wrote the scanner logs to log file: {}".format(
                    logs_file_path))
        finally:
            return logs_file_path

    def scan(self):
        """
        Run the listed atomic scanners on image under test.

        #FIXME: at the moment this menthod is returning the results of multiple
        scanners in one json and sends over the bus
        """
        self.logger.info("Received job : {}".format(self.job_info))

        # TODO: Figure out why random tag (with date) is coming
        # image_under_test=":".join(self.job_info.get("name").split(":")[:-1])
        image_under_test = self.job_info.get("output_image")
        self.logger.info("Image under test:{}".format(image_under_test))
        # copy the job info into scanners data,
        # as we are going to add logs and msg
        scanners_data = self.job_info
        scanners_data["msg"] = {}
        scanners_data["logs_URL"] = {}
        scanners_data["logs_file_path"] = {}

        # pull the image first, if failed move on to start_delivery
        if not self.pull_image_under_test(image_under_test):
            self.logger.info(
                "Image pulled failed, moving job to delivery phase.")
            scanners_data["action"] = "start_delivery"
            return False, scanners_data

        # run the multiple scanners on image under test
        for scanner in self.scanners.keys():
            data_temp = self.run_a_scanner(scanner, image_under_test)

            if not data_temp:
                continue

            # TODO: what to do if the logs writing failed, check status here
            # scanners results file path on NFS
            logs_filepath = self.export_scanner_logs(scanner, data_temp)

            # scanner results logs URL
            logs_URL = logs_filepath.replace(
                constants.LOGS_DIR,
                constants.LOGS_URL_BASE
            )

            # keep the message
            scanners_data["msg"][data_temp["scanner_name"]] = data_temp["msg"]

            # pass the logs filepath via beanstalk tube
            # TODO: change the respective key from logs ==> logs_URL while
            # accessing this
            scanners_data["logs_URL"][data_temp["scanner_name"]] = logs_URL

            # put the logs file name as well here in data
            scanners_data["logs_file_path"][
                data_temp["scanner_name"]] = logs_filepath

        # keep notify_user action in data, even if we are deleting the job,
        # since whenever we will read the response, we should be able to see
        # action
        scanners_data["action"] = "notify_user"

        # after all scanners are ran, remove the image
        self.logger.info("Removing the image: {}".format(image_under_test))
        self.conn.remove_image(image=image_under_test, force=True)
        # TODO: Check here if at least one scanner ran successfully
        self.logger.info("Finished executing all scanners.")

        status_file_path = os.path.join(
            self.job_info["logs_dir"],
            constants.SCANNERS_STATUS_FILE)
        # We export the scanners_status on NFS
        self.export_scanners_status(scanners_data, status_file_path)

        return True, scanners_data
