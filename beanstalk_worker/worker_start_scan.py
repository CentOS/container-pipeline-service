#!/usr/bin/python

import beanstalkc
import constants
import docker
import json
import logging
import os
import shutil
import subprocess
import sys

from Atomic import Atomic, mount
from scanner import Scanner

DOCKER_HOST = "127.0.0.1"
DOCKER_PORT = "4243"
BEANSTALKD_HOST = "BEANSTALK_SERVER"

logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s', '%m-%d %H:%M:%S'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

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
except Exception as e:
    logger.log(level=logging.FATAL, msg="Error connecting to Docker daemon.")


class ScannerRunner(object):
    """
    Scanner runner class handling basic operation and orchestration of
    multiple scanner handlers
    """

    def __init__(self, job_info):
        self.job_info = job_info
        self.atomic_object = Atomic()
        # Receive and send `name_space` key-value as is
        self.job_namespace = job_info.get('name_space')
        self.scanners = {
            "registry.centos.org/pipeline-images/pipeline-scanner": PipelineScanner,
            "registry.centos.org/pipeline-images/scanner-rpm-verify": ScannerRPMVerify,
            "registry.centos.org/pipeline-images/misc-package-updates": MiscPackageUpdates
        }

    def pull_image_under_test(self, image_under_test):
        """
        Pulls image under test on test run host
        """
        logger.log(
                level=logging.INFO,
                msg="Pulling image %s" % image_under_test)
        pull_data = conn.pull(
            repository=image_under_test
        )

        if 'error' in pull_data:
            logger.log(level=logging.FATAL, msg="Couldn't pull requested image")
            logger.log(level=logging.FATAL, msg=pull_data)
            return False
        logger.log(level=logging.INFO, msg="Image is pulled %s" % image_under_test)
        return True

    def run_a_scanner(self, scanner, image_under_test):
        """
        Run the given scanner on image_under_test
        """
        json_data = {}
        # create object for the respective scanner class
        scanner_obj = self.scanners.get(scanner)()
        # should receive the JSON data loaded
        status, json_data = scanner_obj.run(image_under_test)

        if not status:
            logger.log(
                level=logging.WARNING,
                msg="Failed to run the scanner %s" % scanner
            )
        else:
            logger.log(
                level=logging.INFO,
                msg="Finished running %s scanner." % scanner
            )

        # if scanner failed to run, this will return {}, do check at receiver end
        return json_data

    def export_scanner_logs(self, scanner, data):
        """
        Export scanner logs in given directory
        """
        logs_file_path = os.path.join(
                self.job_info["logs_dir"],
                constants.SCANNERS_RESULTFILE[scanner][0])
        logger.log(
                level=logging.INFO,
                msg="Scanner=%s result log file:%s" % (scanner, logs_file_path)
                )
        try:
            fin = open(logs_file_path, "w")
        except IOError as e:
            logger.log(
                level=logging.CRITICAL,
                msg="Failed to write scanner=%s logs on NFS share." % scanner)
            logger.log(
                level=logging.CRITICAL,
                msg=str(e))
        else:
            json.dump(data, fin, indent=4, sort_keys=True)
            logger.log(
                level=logging.INFO,
                msg="Wrote the scanner logs to log file: %s" % logs_file_path
                )
        finally:
            return logs_file_path

    def run(self):
        """"
        Runs the listed atomic scanners on image under test

        #FIXME: at the moment this menthod is returning the results of multiple
        scanners in one json and sends over the bus
        """
        logger.log(level=logging.INFO, msg="Received job : %s" % job_info)

        # TODO: Figure out why random tag (with date) is coming
        # image_under_test = ":".join(self.job_info.get("name").split(":")[:-1])
        image_under_test = self.job_info.get("name")
        logger.log(level=logging.INFO, msg="Image under test:%s" % image_under_test)

        # copy the job info into scanners data,
        # as we are going to add logs and msg
        scanners_data = self.job_info
        scanners_data["msg"] = {}
        scanners_data["logs"] = {}

        # pull the image first, if failed move on to start_delivery
        if not self.pull_image_under_test(image_under_test):
            logger.log(
                level=logging.INFO,
                msg="Image pulled failed, moving job to delivery phase."
            )
            scanners_data["action"] = "start_delivery"
            return False, scanners_data

        # run the multiple scanners on image under test
        for scanner in self.scanners.keys():
            data_temp = self.run_a_scanner(scanner, image_under_test)

            if not data_temp:
                continue

            # TODO: what to do if the logs writing failed, check status here
            logs_filepath = self.export_scanner_logs(scanner, data_temp)

            logs_URL = logs.filepath.replace(
                    constants.LOGS_DIR,
                    constants.LOGS_URL_BASE
                    )

            # keep the message
            scanners_data["msg"][data_temp["scanner_name"]] = data_temp["msg"]
            # pass the logs filepath via beanstalk tube
            scanners_data["logs"][data_temp["scanner_name"]] = logs_URL

        scanners_data["action"] = "notify_user"
        # This field is needed for email worker to hint that this is scan
        # result email and need to move to next phase of delivery
        scanners_data["scan_results"] = True

        # after all scanners are ran, remove the image
        logger.log(
                level=logging.INFO,
                msg="Removing the image: %s" % image_under_test)

        conn.remove_image(image=image_under_test, force=True)

        # TODO: Check here if at least one scanner ran successfully
        logger.log(level=logging.INFO, msg="Finished executing all scanners.")
        return True, scanners_data


class ScannerRPMVerify(object):
    """
    scanner-rpm-verify atomic scanner handler
    """
    def __init__(self):
        self.scanner_name = "scanner-rpm-verify"
        self.full_scanner_name = "registry.centos.org/pipeline-images/scanner-rpm-verify"
        self.atomic_object = Atomic()

    def run_atomic_scanner(self):
        """
        Run the atomic scan command
        """
        process = subprocess.Popen([
            "atomic",
            "scan",
            "--scanner=rpm-verify",
            "%s" % self.image_id
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        # returns out, err
        return process.communicate()

    def run(self, image_under_test):
        """
        Run the scanner-rpm-verify atomic scanner

        Returns: Tuple stating the status of the execution and
        actual data
        (True/False, json_data)
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
                logger.log(
                    level=logging.FATAL,
                    msg="No scan results found at %s" % output_json_file)
                # FIXME: handle what happens in this case
                return False, self.process_output(json_data)
        else:
            # TODO: do not exit here if one of the scanner failed to run,
            # others might run
            logger.log(
                level=logging.FATAL,
                msg="Error running the scanner %s. Error: %s" % (self.scanner_name, err)
            )
            return False, self.process_output(json_data)

        return True, self.process_output(json_data)

    def process_output(self, json_data):
        """
        Process the output from scanner
        """
        data = {}
        data["scanner_name"] = self.scanner_name
        # TODO: More verifcation and validation on the data
        data["msg"] = "RPM verify results."
        data["logs"] = json_data
        return data


class PipelineScanner(object):
    """
    pipeline-scanner atomic scanner handler
    """
    def __init__(self):
        self.scanner_name = "pipeline-scanner"
        self.full_scanner_name = "registry.centos.org/pipeline-images/pipeline-scanner"
        self.atomic_object = Atomic()
        self.mount_object = mount.Mount()

    def mount_image(self):
        """
        Mount image on local file system
        """
        # get the SHA ID of the image.

        self.mount_object.mountpoint = self.image_rootfs_path
        self.mount_object.image = self.image_id

        # mount the rootfs in read-write mode. else yum will fail
        self.mount_object.options = ["rw"]

        # configure options before mounting the image rootfs
        logger.log(level=logging.INFO,
                   msg="Setting up system to mount image's rootfs")

        # create a directory /<image_id> where we'll mount image's rootfs
        try:
            os.makedirs(self.image_rootfs_path)
        except OSError as error:
            logger.log(
                    level=logging.WARNING,
                    msg=str(error)
                    )
            logger.log(
                    level=logging.INFO,
                    msg="Unmounting and removing directory %s " % self.image_rootfs_path
                    )
            try:
                self.mount_object.unmount()
            except Exception as e:
                logger.log(
                    level=logging.WARNING,
                    msg="Failed to unmount path= %s - Error: %s" % (self.image_rootfs_path, str(e))
                    )
            else:
                try:
                    shutil.rmtree(self.image_rootfs_path)
                except Exception as e:
                    logger.log(
                        level=logging.WARNING,
                        msg="Failed to remove= %s - Error: %s" % (self.image_rootfs_path, str(e))
                    )
            # retry once more
            try:
                os.makedirs(self.image_rootfs_path)
            except OSError as error:
                logger.log(
                    level=logging.FATAL,
                    msg=str(error)
                        )
                # fail! and return
                return False

        logger.log(
            level=logging.INFO,
            msg="Mounting rootfs %s on %s" % (self.image_id, self.image_rootfs_path))
        self.mount_object.mount()
        logger.log(level=logging.INFO,
                   msg="Successfully mounted image's rootfs")

        return True

    def unmount_image(self):
        """
        Unmount image using the Atomic mount object
        """
        logger.log(
            level=logging.INFO,
            msg="Unmounting image's rootfs from %s" % self.mount_object.mountpoint)
        # TODO: Error handling and logging
        self.mount_object.unmount()

    def remove_image(self):
        """
        Removes the mounted image rootfs path as well as
        removes the image using docker
        """
        try:
            shutil.rmtree(self.image_rootfs_path)
        except OSError as error:
            logger.log(
                level=logging.WARNING,
                msg="Error removing image rootfs path. %s" % str(error)
                )
        logger.log(
            level=logging.INFO,
            msg="Removing the image %s" % self.image_under_test)
        conn.remove_image(image=self.image_under_test, force=True)

    def run(self, image_under_test):
        """
        Run the scanner
        """
        self.image_under_test = image_under_test
        self.image_id = self.atomic_object.get_input_id(image_under_test)
        self.image_rootfs_path = os.path.join("/", self.image_id)

        json_data = {}

        if not self.mount_image():
            return False, json_data

        cmd = [
            'atomic',
            'scan',
            "--scanner=%s" % self.scanner_name,
            "--rootfs=%s" % self.image_rootfs_path,
            "%s" % self.image_id
        ]

        logger.log(
            level=logging.INFO,
            msg="Executing atomic scan:  %s" % " ".join(cmd)
            )

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
            )

        out, err = process.communicate()

        if out != "":
            # TODO: hacky and ugly. figure a better way
            # https://github.com/projectatomic/atomic/issues/577
            output_json_file = os.path.join(
                out.strip().split()[-1].split('.')[0],
                "_%s" % self.image_rootfs_path.split('/')[1],
                SCANNERS_OUTPUT[self.full_scanner_name][0]
            )
            logger.log(
                level=logging.INFO,
                msg="Result file: %s" % output_json_file
            )

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
            else:
                logger.log(level=logging.FATAL,
                           msg="No scan results found at %s" % output_json_file)
                return False, json_data
        else:
            logger.log(
                level=logging.WARNING,
                msg="Failed to get the results from atomic CLI. Error:%s" % err
            )
            return False, json_data

        self.unmount_image()
        shutil.rmtree(self.image_rootfs_path, ignore_errors=True)
        logger.log(
            level=logging.INFO,
            msg="Finished executing scanner: %s" % self.scanner_name)
        return True, self.process_output(json_data)

    def process_output(self, json_data):
        """
        Process the output from the scanner, parse the json and
        add meaningful information based on validations
        """
        data = {}
        data["scanner_name"] = self.scanner_name
        if json_data["Scan Results"]["Package Updates"]:
            data["logs"] = json_data
            data["msg"] = "Container image requires update."
        else:
            data["logs"] = {}
            data["msg"] = "No updates required."
        return data


class MiscPackageUpdates(Scanner):
    def __init__(self):
        self.scanner_name = "misc-package-updates"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/misc-package-updates"
        self.scan_types = ["pip-updates", "npm-updates", "gem-updates"]

    def run(self, image_under_test):
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        logs = []
        super(MiscPackageUpdates, self).__init__(
            image_under_test=image_under_test,
            scanner_name=self.scanner_name,
            full_scanner_name=self.full_scanner_name,
            to_process_output=False
        )

        os.environ["IMAGE_NAME"] = self.image_under_test

        for _ in self.scan_types:
            scan_cmd = [
                "atomic",
                "scan",
                "--scanner={}".format(self.scanner_name),
                "--scan_type={}".format(_),
                "{}".format(image_under_test)
            ]

            scan_results = super(MiscPackageUpdates, self).run(scan_cmd)

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
        data["msg"] = "Results for miscellaneous package manager updates"
        data["logs"] = logs

        return data

bs = beanstalkc.Connection(host=BEANSTALKD_HOST)
bs.watch("start_scan")


while True:
    try:
        job = bs.reserve()
        job_info = json.loads(job.body)
        scan_runner_obj = ScannerRunner(job_info)
        status, scanners_data = scan_runner_obj.run()
        if not status:
            logger.log(
                level=logging.CRITICAL,
                msg="Failed to run scanners on image under test, moving on!"
            )
    except Exception as e:
        logger.log(level=logging.FATAL, msg=str(e))
    finally:
        bs.use("master_tube")
        job_id = bs.put(json.dumps(scanners_data))

        logger.log(
            level=logging.INFO,
            msg="Job moved from scan phase, id: %s" % job_id
            )
        job.delete()
