#!/usr/bin/python
"""
This class is for checking container capabilities.

It reuses the scanner class for the methods.
"""

import os

from container_pipeline.workers.scanners.base import Scanner


class ContainerCapabilities(Scanner):
    """Container Capabilities scan."""

    def __init__(self):
        """Scanner name and types."""
        self.scanner_name = "container-capabilities-scanner"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/" \
            "container-capabilities-scanner"
        self.scan_types = ["check-capabilities"]

    def scan(self, image_under_test):
        """Run the scanner on image under test."""
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

        if not scan_results[0]:
            return False, None

        logs.append(scan_results[1])

        return True, self.process_output(logs)

    def process_output(self, logs):
        """
        Process the output logs to send to other workers.

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
