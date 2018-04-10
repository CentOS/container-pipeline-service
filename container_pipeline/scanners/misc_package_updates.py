#!/usr/bin/python
"""This class is for checking updates from different other packagers."""

import os

from container_pipeline.scanners.base import Scanner


class MiscPackageUpdates(Scanner):
    """Checks updates for packages other than RPM."""

    def __init__(self):
        """
        Initialize scanner invoker with basic configs
        """
        self.scanner = "misc-package-updates"
        self.scan_types = ["pip-updates", "npm-updates", "gem-updates"]
        self.result_file = "misc_package_updates_scanner_results.json"

    def run(self, image):
        """Run the scanner."""
        super(MiscPackageUpdates, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file)

        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        logs = []
        os.environ["IMAGE_NAME"] = self.image

        for st in self.scan_types:
            # scan_results gets {"status": True/False,
            #                    "logs": {},
            #                    "msg": msg}
            scan_results = self.scan(scan_type=st, process_output=False)

            if not scan_results.get("status", False):
                continue

            logs.append(scan_results["logs"])

        # invoke base class's cleanup utility
        self.cleanup()

        return self.process_output(logs)

    def process_output(self, logs):
        """
        Genaralising output.

        Processing data for this scanner is unlike other scanners
        because, for this scanner we need to send logs of three
        different scan types of same atomic scanner unlike other
        atomic scanners which have only one, and hence treated
        as default, scan type
        """
        data = {}
        data["image_under_test"] = self.image
        data["scanner"] = self.scanner
        data["logs"] = logs
        # if not logs found, write proper msg and return
        if not logs:
            data["msg"] = "Failed to run the scanner."
            return data
        # initialize with empty string for concatenation
        data["msg"] = ""
        for i in logs:
            data["msg"] += i.get("Summary", "Faled to run the scanner.")
        return data
