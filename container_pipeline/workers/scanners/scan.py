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

from container_pipeline.workers.scanners.runner import ScannerRunner

class ScanWorker(BaseWorker):
    """Scan worker"""

    def handle_job(self, job):
        """
        This scans the images for the job requests in start_scan tube.
        this cals the ScannerRunner for performing the scan work
        """

        debug_logs_file = os.path.join(
            job_info["logs_dir"], "service_debug.log")
        dfh = config.DynamicFileHandler(logger, debug_logs_file)

        self.logger.info('Got job: %s' % job)
        scan_runner_obj = ScannerRunner(job)
        status, scanners_data = scan_runner_obj.scan()
        if not status:
            logger.critical(
                "Failed to run scanners on image under test, moving on!"
            )
        else:
            self.logger.info(str(scanners_data))

        # Remove the msg and logs from the job_info as they are not
        # needed now
        scanners_data.pop("msg", None)
        scanners_data.pop("logs", None)
        scanners_data.pop("scan_results", None)

        # if weekly scan, push the job for notification
        if job.get("weekly"):
            scanners_data["action"] = "notify_user"
            self.queue.put(json.dumps(scanners_data), 'master_tube')
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            # change the action
            scanners_data["action"] = "start_delivery"
            # Put the job details on central tube
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.logger.info("Put job for delivery on master tube")

        # remove per file build log handler from logger
        if 'dfh' in locals():
            dfh.remove()

if __name__ == '__main__':
    DOCKER_HOST = "127.0.0.1"
    DOCKER_PORT = "4243"

    load_logger()
    logger = logging.getLogger("scan-worker")

    SCANNERS_OUTPUT = {
        "registry.centos.org/pipeline-images/pipeline-scanner": [
            "image_scan_results.json"],
        "registry.centos.org/pipeline-images/scanner-rpm-verify": [
            "RPMVerify.json"]}

    try:
        # docker client connection to CentOS 7 system
        conn = docker.Client(base_url="tcp://%s:%s" % (
            DOCKER_HOST, DOCKER_PORT
        ))
        worker = ScanWorker(logger, sub='start_scan', pub='failed_scan')
        worker.run()
    except Exception as e:
        logger.fatal("Error connecting to Docker daemon.", exc_info=True)
