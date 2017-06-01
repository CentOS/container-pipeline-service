#!/usr/bin/env python

# This file contains a class `Scanner` that can be used as super class for
# other scanners in the project to avoid duplication of code

import json
import logging
import os
import subprocess
import sys

from Atomic import Atomic
from constants import SCANNERS_OUTPUT


logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)


class Scanner(object):
    def __init__(self, image_under_test, scanner_name, full_scanner_name,
                 to_process_output):
        # to be provided by child class
        self.scanner_name = scanner_name
        self.full_scanner_name = full_scanner_name
        self.image_under_test = image_under_test

        # Scanner class's own attributes
        self.atomic_obj = Atomic()
        self.image_id = self.atomic_obj.get_input_id(self.image_under_test)
        self.to_process_output = to_process_output

    def run_atomic_scanner(self, cmd):
        """
        Run the scanner with the cmd provided by child class
        """
        process = subprocess.Popen(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        # returns out, err
        return process.communicate()

    def scan(self, cmd):
        # self.image_under_test = image_under_test
        # self.image_id = self.atomic_obj.get_input_id(self.image_under_test)

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
                logger.log(
                    level=logging.FATAL,
                    msg="No scan results found at {}".format(output_json_file)
                )
                return False, json_data
        else:
            logger.log(
                level=logging.FATAL,
                msg="Error running the scanner {}. Error {}".format(
                    self.scanner_name,
                    err
                )
            )
            return False, json_data

        if self.to_process_output:
            return True, self.process_output(json_data)
        return True, json_data

    def process_output(self, json_data):
        """
        Process the output from scanner
        """
        data = {}

        data["scanner_name"] = self.scanner_name

        data["msg"] = "{} results.".format(self.scanner_name)
        data["logs"] = json_data
        return data
