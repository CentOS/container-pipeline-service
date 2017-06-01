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

class ContainerCapabilities(Scanner):
    def __init__(self):
        self.scanner_name = "container-capabilities-scanner"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/" \
            "container-capabilities-scanner"
        self.scan_types = ["check-capabilities"]

    def scan(self, image_under_test):
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        logs = []
        super(ContainerCapabilities, self).__init__(
            image_under_test=image_under_test,
            scanner_name=self.scanner_name,
            full_scanner_name=self.full_scanner_name,
            to_process_output=False
        )

        os.environ["IMAGE_NAME"] = self.image_under_test

        # Jfor _ in self.scan_types:
        scan_cmd = [
            "atomic",
            "scan",
            "--scanner={}".format(self.scanner_name),
            "--scan_type={}".format(self.scan_types[0]),
            "{}".format(image_under_test)
        ]

        scan_results = super(ContainerCapabilities, self).scan(scan_cmd)

        if scan_results[0] != True:
            return False, None

        logs.append(scan_results[1])

        return True, self.process_output(logs)

    def process_output(self, logs):
        """
        Processing data for this scanner is unlike other scanners because, for
        this scanner we need to send logs of three different scan types of same
        atomic scanner unlike other atomic scanners which have only one, and
        hence treated as default, scan type
        """
        data = {}
        data["scanner_name"] = self.scanner_name
        data["msg"] = "Results for container capabilities scanner"
        data["logs"] = logs

        return data
