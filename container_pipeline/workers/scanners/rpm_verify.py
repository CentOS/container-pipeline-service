#!/usr/bin/python
"""RPM Verify Scan Class."""

import json
import logging
import os
import subprocess

from Atomic import Atomic
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.settings import SCANNERS_OUTPUT


class ScannerRPMVerify(object):
    """scanner-rpm-verify atomic scanner handler."""

    def __init__(self):
        """Scanner verify initialization."""
        self.scanner_name = "scanner-rpm-verify"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/scanner-rpm-verify"
        self.atomic_object = Atomic()

        # Add logger
        load_logger()
        self.logger = logging.getlogger('scan-worker')

    def run_atomic_scanner(self):
        """Run the atomic scan command."""
        process = subprocess.Popen([
            "atomic",
            "scan",
            "--scanner=rpm-verify",
            "{}".format(self.image_id)
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # returns out, err
        return process.communicate()

    def scan(self, image_under_test):
        """
        Run the scanner-rpm-verify atomic scanner.

        Returns: Tuple stating the status of the execution and
        actual data(True/False, json_data)

        """
        self.image_under_test = image_under_test
        self.image_id = self.atomic_object.get_input_id(self.image_under_test)

        json_data = {}
        out, err = self.run_atomic_scanner()
        if out != "":
            output_json_file = os.path.join(
                out.strip().split()[-1].split('.')[0],
                self.image_id,
                # TODO: provision parsing multiple output files per scanner
                SCANNERS_OUTPUT[self.full_scanner_name][0]
            )

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
            else:
                self.logger.critical(
                    "No scan results found at {}".format(output_json_file))
                # FIXME: handle what happens in this case
                return False, self.process_output(json_data)
        else:
            # TODO: do not exit here if one of the scanner failed to run,
            # others might run
            self.logger.critical(
                "Error running the scanner {}. Error: {}".format(
                    self.scanner_name, err))
            return False, self.process_output(json_data)

        return True, self.process_output(json_data)

    def process_output(self, json_data):
        """Process the output from scanner."""
        data = {}
        data["scanner_name"] = self.scanner_name
        # TODO: More verifcation and validation on the data
        data["msg"] = "RPM verify results."
        data["logs"] = json_data
        return data
