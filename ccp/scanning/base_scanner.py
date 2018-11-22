"""
This module has Base scanner class with needed functionalities
for sub-scanners.
"""


from datetime import datetime

import logging
import os
import platform
import subprocess


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

        :return: Returns the absolute path of binary in system or None
                 if binary is absent in the system
        :rtype: str
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
        return None

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
