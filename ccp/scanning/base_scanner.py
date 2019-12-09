"""
This module has Base scanner class with needed functionalities
for sub-scanners.
"""


from datetime import datetime

import json
import logging
import os
import platform
import subprocess
import sys

import requests


class BinaryDoesNotExist(Exception):
    """
    Exception in cases where the binary needed by the scanner
    doesn't exist in the system
    """
    pass


class BaseScanner(object):
    """
    BaseScanner class for sub-scanners to inherit, with needed
    functionalities and methods which can be implemented by sub-scanners.
    """
    # scanner name
    NAME = ''
    DESCRIPTION = ''

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger('console')
        if not self.NAME:
            raise Exception("Define name of your scanner class!")
        if not self.DESCRIPTION:
            raise Exception("Specify description of your scanner!")
        self.output_format = {
            "scanner": self.NAME,
            "scanner_description": self.DESCRIPTION,
            "image_under_test": "",
            "scan_type": "",
            "successful": "",
            "alert": "",
            "start_time": "",
            "end_time": "",
            "os": "",
            "message": "",
            "logs": "",
        }

    def which(self, binary):
        """
        Finds the absolute path of the given binary

        :param binary: Binary name example: npm
        :type binary: str

        :return: Returns the absolute path of binary in system
        :rtype: str
        :raise BinaryDoesNotExist: If given binary is invalid or not found
                                   in the system, this exception is raised.
        """
        def is_executable(fpath):
            """
            Check whether the specified path is a file and has executable
            permissions set
            :param fpath: Path of the binary
            :param fpath: str
            :return: True if given path is file and has executable permission
            """
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        # split the base path and filename
        fpath, fname = os.path.split(binary)
        # checks if the base path is present (in case for eg: /usr/bin/npm)
        if fpath:
            # checks whether absolute path of provided binary is executable
            if is_executable(binary):
                # if it exists and executable return same path
                return binary
        # the provided binary is not absolute path, so we need to check for
        # its existence by appending it to system PATH
        else:
            # iterate over each PATH env var value
            for path in os.environ["PATH"].split(os.pathsep):
                # generate the absolute path for checking its existence
                exe_file = os.path.join(path, binary)
                if is_executable(exe_file):
                    return exe_file
        # if not returned above, it means, the file doesn't exist
        raise BinaryDoesNotExist("{} is not installed in the system.".format(
            binary))

    def run(self):
        """
        This method is called to run the scanner operation.
        """
        raise NotImplementedError

    def linux_distribution(self):
        """
        Returns the Linux distribution details
        """
        return ' '.join(platform.linux_distribution())

    def time_now(self, time_format="%Y-%m-%d-%H-%M-%S-%f"):
        """
        Returns the current time

        :param time_format: Format of time Default: "%Y-%m-%d %H:%M:%S.%f"
        :type time_format: str

        :return: Current time as per given time_Format
        """

        return datetime.now().strftime(time_format)

    def run_cmd(self, cmd, shell=False):
        """
        Runs a shell command.

        :param cmd: Command to run
        :param shell: Whether to run raw shell commands with '|'
                      and redirections
        :type cmd: str
        :type shell: boolean

        :return: Command output
        :rtype: str
        :raises: subprocess.CalledProcessError
        """
        if shell:
            return subprocess.check_output(cmd, shell=True)
        else:
            return subprocess.check_output(cmd.split(), shell=False)

    def run_cmd_out_err(self, cmd):
        """
        Runs a shell command and returns output & error (if any)

        :param cmd: Command to run
        :type cmd: tuple or list

        :return: Command output
        :rtype: str, int
        """
        return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()

    def post_request(self, endpoint, api, data, headers=None):
        """
        Make a post call to analytics server with given data
        :param endpoint: API server end point
        :param api: API to make POST call against
        :param data: JSON data needed for POST call to api endpoint
        :return: Tuple (status, error_if_any, status_code)
                 where status = True/False
                       error_if_any = string message on error, "" on success
                       status_code = status_code returned by server
        """
        url = requests.compat.urljoin(endpoint, api)
        # TODO: check if we need API key in data
        try:
            r = requests.post(
                url,
                json.dumps(data),
                headers=headers)
        except requests.exceptions.RequestException as e:
            error = ("Could not send POST request to URL {0}, "
                     "with data: {1}.").format(url, str(data))
            return False, error + " Error: " + str(e), 0
        else:
            # requests.codes.ok == 200
            if r.status_code == requests.codes.ok:
                return True, json.loads(r.text), r.status_code
            else:
                return False, "Returned {} status code for {}".format(
                    r.status_code, url), r.status_code

    def get_request(self, endpoint, api, data, headers=None):
        """
        Make a get call to analytics server
        :param endpoint: API server end point
        :param api: API to make GET call against
        :param data: JSON data needed for GET call
        :return: Tuple (status, error_if_any, status_code)
                 where status = True/False
                       error_if_any = string message on error, "" on success
                       status_code = status_code returned by server
        """
        url = requests.compat.urljoin(endpoint, api)
        # TODO: check if we need API key in data
        try:
            r = requests.get(
                url,
                params=data,
                headers=headers)

        except requests.exceptions.RequestException as e:
            error = "Failed to process URL: {} with params {}".format(
                    url, data)
            return False, error + " Error: " + str(e), 0
        else:
            # requests.codes.ok == 200 or
            # check for 400 code - as this is a valid response
            # as per the workflow
            if r.status_code in [requests.codes.ok, 400]:
                return True, json.loads(r.text), r.status_code
            else:
                msg = "Returned {} status code for {}. {}".format(
                    r.status_code, url, r.json().get(
                        "summary", "no summary returned from server."))
                return False, msg, r.status_code

    def export_json_results(self, results, output_dir, output_file):
        """
        Export given results JSON data in output_dir/output_file

        :param results: JSON results to be exported
        :type results: dict
        :param output_dir: Output directory
        :type output_dir: str
        :param output_file: Output file name
        :type output_file: str
        """
        os.makedirs(output_dir)

        result_filename = os.path.join(output_dir, output_file)

        with open(result_filename, "w") as f:
            json.dump(results, f, indent=4, separators=(",", ": "))

    def template_json_data(self, scanner, scan_type='', uuid=''):
        """
        Populate and return a template standard json data out for scanner.
        """
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        json_out = {
            "Start Time": current_time,
            "Successful": False,
            "Scan Type": scan_type,
            "UUID": uuid,
            "Scanner": scanner,
            "Scan Results": {},
            "Summary": ""
        }
        return json_out

    def configure_stdout_logging(
            self, logger_name, logging_level=logging.DEBUG):
        """
        Configures stdout logging and returns logger object

        :param logger_name: Logger name
        :type logger_name: str
        :param logging_level: Logging level
        :type logging_level: str or int

        :return: Logger object
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging_level)
        # add sys.stdout stream
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        # add logging formatter
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s p%(process)s %(name)s %(lineno)d "
            "%(levelname)s - %(message)s"
        )
        # set formatter to stream handler
        ch.setFormatter(formatter)
        # set handler to logger
        logger.addHandler(ch)
        return logger

    def get_env_var(self, env_var):
        """
        Gets the given configured env_var
        :param env_var: Environment variable to be accessed
        :type env_var: str

        :return: Value of given env_var
        :rtype: str
        """
        if not os.environ.get(env_var, False):
            raise ValueError(
                "No value for {0} env var. Please re-run with: "
                "{0}=<VALUE> [..] atomic scan [..] ".format(env_var)
            )
        return os.environ.get(env_var)
