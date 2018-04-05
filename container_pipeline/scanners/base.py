#!/usr/bin/env python

"""
This file has Scanning base class, with helper utilities.
Per scanner, a subsclass can be written and use Scanner class as
base class.
"""

import json
import logging
import os
import shutil
import subprocess

from Atomic import Atomic, mount

from container_pipeline.lib.log import load_logger


class Scanner(object):
    """This is the base class for all the scanners.

    Other classes can use as super class for common functions.
    """

    def __init__(self, image, scanner, result_file):
        # container/image under test
        self.image = image
        # scanner name / as installed /not full URL
        self.scanner = scanner
        # name of the output result file by scanner
        self.result_file = result_file
        # image_id
        self.image_id = Atomic().get_input_id(self.image)
        # set logger or set console
        load_logger()
        self.logger = logging.getLogger("scan-worker")
        # Flag to indicate if image is mounted on local filesystem
        self.is_mounted = False
        # image mount path
        self.image_mountpath = os.path.join("/", self.image_id)
        # initialize the atomic mount object
        self.mount_obj = mount.Mount()
        # provide image id to mount object
        self.mount_obj.image = self.image_id
        # provide mount option read/write
        self.mount_obj.options = ["rw"]

    def run_cmd(self, cmd):
        """
        Runs a shell command and returns output & error (if any)

        :param cmd: Command to run
        :type cmd: tuple or list

        :return: Command output and error
        """
        return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()

    def make_dirs(self, path):
        """
        Create directories
        """
        try:
            os.makedirs(path)
        except OSError as error:
            self.logger.critical("Failed to create dir {}. {}".format(
                path, error))
            return False
        else:
            return True

    def remove_dirs(self, path):
        """
        Remove given dir path
        """
        if not os.path.isdir(path):
            self.logger.warning("Path={} is not dir.".format(path))
            return False

        try:
            shutil.rmtree(path)
        except OSError as e:
            self.logger.warning("Failed to remove dir={}. {}".format(path, e))
            return False
        else:
            return True

    def unmount_image(self):
        """
        Umount mounted image
        """
        try:
            self.mount_obj.unmount()
        except Exception as e:
            self.logger.warning("Failed to unmount={}. {}".format(
                self.image_mountpath, e))
            return False
        else:
            self.logger.debug("Unmounted path={}".format(self.image_mountpath))
            return True

    def clean_mountpath(self):
        """
        Remove existing mount point if exists
        """
        # first check if mount point exists
        if os.path.isdir(self.image_mountpath):
            # first try to remove the dir
            if self.remove_dirs(self.image_mountpath):
                # removed mount_path dir if it existed
                return True
            else:
                self.logger.warning("Mount path={} exists.".format(
                    self.image_mountpath))
                self.logger.debug(
                    "Unmounting path={}".format(self.image_mountpath))
                if not self.unmount_image():
                    self.logger.critical(
                        "Mount path={} already exist and in use.".format(
                            self.image_mountpath))
                    # failed to unmount, return False
                    return False
                else:
                    # now we have unmounted, try removing dirs
                    if self.remove_dirs(self.image_mountpath):
                        return True
                    else:
                        # even after unmount, it couldnt remove dirs
                        return False
        else:
            # mount path is ready to mount
            return True

    def mount_image(self):
        """
        Mount image under test
        """
        # if image is already mounted return
        if self.is_mounted:
            return True

        # clean up the mount point
        if not self.clean_mountpath():
            self.logger.critical(
                "Mount path={} is not ready for mount.".format(
                    self.image_mountpath))
            return False

        # create mount point directory
        if not self.make_dirs(self.image_mountpath):
            # couldnt create dir
            self.logger.critical(
                "Failed to create dir for mount path={}".format(
                    self.image_mountpath))
            return False

        # now using mount object, mount the image
        try:
            self.mount_obj.mount()
        except Exception as e:
            self.logger.critical(
                "Failed to mount at path={}. {}".format(
                    self.image_mountpath, str(e)))
            # set the mount flag
            self.is_mounted = False
            return False
        else:
            # set the mount flag
            self.is_mounted = True
            self.logger.debug(
                "Mounted image at path={}".format(self.image_mountpath))
            return True

    def read_json(self, file_path):
        """
        read the json file
        """
        if not os.path.isfile(file_path):
            self.logger.critical("File={} does not exist.".format(file_path))
            return None
        try:
            data = json.loads(open(file_path).read())
        except Exception as e:
            self.logger.critical("Failed to open/read file={}. {}".format(
                file_path, str(e)))
            return None
        else:
            return data

    def parse_result_path(self, stdout, rootfs=False):
        """
        Parse the path to result dir and find report inside it
        from given stdout
        """
        lines = stdout.strip().split()
        if not lines:
            return None
        # last line of stdout has path of result dir
        # log the result dir, as we can remove this as part of cleanup
        self.res_dir = lines[-1].split('.')[0]

        # if its output of scanner which needs mount
        if rootfs:
            res_file = os.path.join(
                self.res_dir,
                "_{}".format(self.image_mountpath.split("/")[1]),
                self.result_file)
        # or if its a scan without mount
        else:
            res_file = os.path.join(
                self.res_dir,
                self.image_id,
                self.result_file)

        return res_file

    def process_output(self, result):
        """
        Process the output from scanner, and format is as per need.
        """
        # grab the summary of scanper as msg of output
        msg = result.get("Summary",
                         result.get("msg",
                                    "{} results".format(self.scanner)))
        return {
            "image_under_test": self.image,
            "scanner": self.scanner,
            "msg": msg,
            "logs": result.get("logs", {}),
            "status": result.get("status", False)
        }

    def scan(self, scan_type=None,
             rootfs=None, verbose=False, process_output=True):
        """
        Runs atomic scan for given scan_type
        """
        cmd = ["atomic", "scan", "--scanner={}".format(self.scanner)]

        if scan_type:
            cmd.append("--scan_type={}".format(scan_type))

        if rootfs:
            cmd.append("--rootfs={}".format(self.image_mountpath))

        if verbose:
            cmd.append("--verbose")

        cmd.append(self.image)

        # Running the atomic scan command after processing params
        self.logger.debug("Running atomic scan: {}".format(str(cmd)))
        out, error = self.run_cmd(cmd)

        result = None
        if out != "":
            res_file = self.parse_result_path(out, rootfs)
            # if scanner did not export the results
            if not res_file:
                msg = "No scan results found for {}".format(self.scanner)
                self.logger.critical(msg)
                result = {"msg": msg, "status": False, "logs": {}}
            else:
                # if scanner exported the result file
                result = self.read_json(res_file)
                # if failed to read the result file or its empty
                if not result:
                    result = {
                        "msg": "Failed to read {} result file.".format(
                            self.scanner),
                        "status": False,
                        "logs": {}}
                # if scanner result is read
                else:
                    result = {"status": True,
                              "logs": result,
                              "msg": "{} results".format(self.scanner)}
        else:
            # if there are issues in executing scanner itself
            self.logger.critical(
                "Error running scanner {}. {}".format(
                    self.scanner, str(error)))
            result = {"msg": "Failed to run scanner {}.".format(self.scanner),
                      "status": False,
                      "logs": {}}

        if process_output:
            return self.process_output(result)
        return result

    def remove_result_dir(self):
        """
        Remove the default location of results by atomic scan
        """
        if os.path.isdir(self.res_dir):
            try:
                shutil.rmtree(self.res_dir)
            except OSError as e:
                self.logger.debug(
                    "Failed to remove dir {}. {}".format(self.res_dir, str(e)))
            else:
                self.logger.debug(
                    "Removed redundant atomic scan results {}".format(
                        self.res_dir))

    def cleanup(self, unmount=False):
        """
        Clean up utilities
         - Removes redundant atomic scan results at `atomic` default location
         - Unmounts if image rootfs is mounted and removes the mount path dir
        """
        self.remove_result_dir()
        if unmount:
            self.unmount_image()
            self.clean_mountpath()
            self.remove_dirs(self.image_mountpath)
