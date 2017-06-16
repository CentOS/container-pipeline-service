#!/usr/bin/env python

"""
This file contains a class Scanner that can be used as super class.

This is for other scanners in the project to avoid duplication of code.
"""

import json
import logging
import os
import subprocess

from Atomic import Atomic
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.settings import SCANNERS_OUTPUT


class Scanner(object):
    """This is the base class for all the scanners.

    Other classes can use as super class for common functions.
    """

    def __init__(self, image_under_test, scanner_name, full_scanner_name,
                 to_process_output):
        """Scanner initialization."""
        # to be provided by child class
        self.scanner_name = scanner_name
        self.full_scanner_name = full_scanner_name
        self.image_under_test = image_under_test

        # Scanner class's own attributes
        self.image_id = Atomic().get_input_id(self.image_under_test)
        self.to_process_output = to_process_output

        # Add logger
        load_logger()
        self.logger = logging.getLogger('scan-worker')

    def run_atomic_scanner(self, cmd):
        """Run the scanner with the cmd provided by child class."""
        process = subprocess.Popen(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        # returns out, err
        return process.communicate()

    def scan(self, cmd):
        """Runner for the child scanner."""
        json_data = {}

        out, err = self.run_atomic_scanner(cmd)

        if out != "":
            output_json_file = os.path.join(
                out.strip().split()[-1].split('.')[0],
                self.image_id,
                SCANNERS_OUTPUT[self.full_scanner_name][0]
            )

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
            else:
                self.logger.critical(
                    "No scan results found at {}".format(output_json_file))
                return False, json_data
        else:
            self.logger.critical(
                "Error running the scanner {}. Error {}".format(
                    self.scanner_name, err))
            return False, json_data

        if self.to_process_output:
            return True, self.process_output(json_data)
        return True, json_data

    def process_output(self, json_data):
        """Process the output from scanner."""
        data = {}

        data["scanner_name"] = self.scanner_name

        data["msg"] = "{} results.".format(self.scanner_name)
        data["logs"] = json_data
        return data
