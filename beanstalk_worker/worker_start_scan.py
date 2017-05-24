#!/usr/bin/python

import beanstalkc
import constants
import docker
import json
import logging
import os
import shutil
import subprocess
import config

from Atomic import Atomic, mount
from scanner import Scanner

DOCKER_HOST = "127.0.0.1"
DOCKER_PORT = "4243"
BEANSTALKD_HOST = "BEANSTALK_SERVER"

config.load_logger()
logger = logging.getLogger("scan-worker")

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
    logger.fatal("Error connecting to Docker daemon.", exc_info=True)


class ScannerRunner(object):
    """
    Scanner runner class handling basic operation and orchestration of
    multiple scanner handlers
    """

    def __init__(self, job_info):
        self.job_info = job_info
        self.atomic_object = Atomic()
        # Receive and send `namespace` key-value as is
        self.job_namespace = job_info.get('namespace')
        self.scanners = {
            "registry.centos.org/pipeline-images/pipeline-scanner":
            PipelineScanner,
            "registry.centos.org/pipeline-images/scanner-rpm-verify":
            ScannerRPMVerify,
            "registry.centos.org/pipeline-images/misc-package-updates":
            MiscPackageUpdates,
            "registry.centos.org/pipeline-images/"
            "container-capabilities-scanner":
            ContainerCapabilities
        }

    def pull_image_under_test(self, image_under_test):
        """
        Pulls image under test on test run host
        """
        logger.info("Pulling image %s" % image_under_test)
        pull_data = conn.pull(
            repository=image_under_test
        )

        if 'error' in pull_data:
            logger.fatal("Error pulling requested image {}: {}".format(
                image_under_test, pull_data
            ))
            return False
        logger.info("Image is pulled %s" % image_under_test)
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
            logger.warning("Failed to run the scanner %s" % scanner)
        else:
            logger.info("Finished running %s scanner." % scanner)

        # if scanner failed to run, this will return {}, do check at receiver
        # end
        return json_data

    def export_scanners_status(self, status, status_file_path):
        """
        Export status of scanners execution for build in process
        """
        try:
            fin = open(status_file_path, "w")
            json.dump(status, fin)
        except IOError as e:
            logger.critical("Failed to write scanners status on NFS share.")
            logger.critical(str(e))
        else:
            logger.info(
                "Wrote scanners status to file: %s" % status_file_path)

    def export_scanner_logs(self, scanner, data):
        """
        Export scanner logs in given directory
        """
        logs_file_path = os.path.join(
            self.job_info["logs_dir"],
            constants.SCANNERS_RESULTFILE[scanner][0])
        logger.info(
            "Scanner=%s result log file:%s" % (scanner, logs_file_path)
        )
        try:
            fin = open(logs_file_path, "w")
            json.dump(data, fin, indent=4, sort_keys=True)
        except IOError as e:
            logger.critical(
                "Failed to write scanner=%s logs on NFS share." % scanner)
            logger.critical(str(e), exc_info=True)
        else:
            logger.info(
                "Wrote the scanner logs to log file: %s" % logs_file_path)
        finally:
            return logs_file_path

    def run(self):
        """"
        Runs the listed atomic scanners on image under test

        #FIXME: at the moment this menthod is returning the results of multiple
        scanners in one json and sends over the bus
        """
        logger.info("Received job : %s" % self.job_info)

        # TODO: Figure out why random tag (with date) is coming
        # image_under_test=":".join(self.job_info.get("name").split(":")[:-1])
        image_under_test = self.job_info.get("output_image")
        logger.info("Image under test:%s" % image_under_test)
        # copy the job info into scanners data,
        # as we are going to add logs and msg
        scanners_data = self.job_info
        scanners_data["msg"] = {}
        scanners_data["logs_URL"] = {}
        scanners_data["logs_file_path"] = {}

        # pull the image first, if failed move on to start_delivery
        if not self.pull_image_under_test(image_under_test):
            logger.info("Image pulled failed, moving job to delivery phase.")
            scanners_data["action"] = "start_delivery"
            return False, scanners_data

        # run the multiple scanners on image under test
        for scanner in self.scanners.keys():
            data_temp = self.run_a_scanner(scanner, image_under_test)

            if not data_temp:
                continue

            # TODO: what to do if the logs writing failed, check status here
            # scanners results file path on NFS
            logs_filepath = self.export_scanner_logs(scanner, data_temp)

            # scanner results logs URL
            logs_URL = logs_filepath.replace(
                constants.LOGS_DIR,
                constants.LOGS_URL_BASE
            )

            # keep the message
            scanners_data["msg"][data_temp["scanner_name"]] = data_temp["msg"]

            # pass the logs filepath via beanstalk tube
            # TODO: change the respective key from logs ==> logs_URL while
            # accessing this
            scanners_data["logs_URL"][data_temp["scanner_name"]] = logs_URL

            # put the logs file name as well here in data
            scanners_data["logs_file_path"][
                data_temp["scanner_name"]] = logs_filepath

        # keep notify_user action in data, even if we are deleting the job,
        # since whenever we will read the response, we should be able to see
        # action
        scanners_data["action"] = "notify_user"

        # after all scanners are ran, remove the image
        logger.info("Removing the image: %s" % image_under_test)
        conn.remove_image(image=image_under_test, force=True)
        # TODO: Check here if at least one scanner ran successfully
        logger.info("Finished executing all scanners.")

        status_file_path = os.path.join(
            self.job_info["logs_dir"],
            constants.SCANNERS_STATUS_FILE)
        # We export the scanners_status on NFS
        self.export_scanners_status(scanners_data, status_file_path)

        return True, scanners_data


class ScannerRPMVerify(object):
    """
    scanner-rpm-verify atomic scanner handler
    """

    def __init__(self):
        self.scanner_name = "scanner-rpm-verify"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/scanner-rpm-verify"
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
                self.clean_scanner_result(output_json_file)
            else:
                logger.fatal("No scan results found at %s" % output_json_file)
                # FIXME: handle what happens in this case
                return False, self.process_output(json_data)
        else:
            # TODO: do not exit here if one of the scanner failed to run,
            # others might run
            logger.fatal(
                "Error running the scanner %s. Error: %s" % (
                    self.scanner_name, err))
            return False, self.process_output(json_data)

        return True, self.process_output(json_data)

    def clean_scanner_result(self, path):
        """
        Clean the scanner  results from /var/lib/atomic directory
        """
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Failed to remove %s" % path)
            logger.warning("Error: %s" % str(e))

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
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/pipeline-scanner"
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
        logger.info("Setting up system to mount image's rootfs")

        # create a directory /<image_id> where we'll mount image's rootfs
        try:
            os.makedirs(self.image_rootfs_path)
        except OSError as error:
            logger.warning(msg=str(error), exc_info=True)
            logger.info(
                "Unmounting and removing directory %s "
                % self.image_rootfs_path)
            try:
                self.mount_object.unmount()
            except Exception as e:
                logger.warning(
                    "Failed to unmount path= %s - Error: %s" % (
                        self.image_rootfs_path, str(e)),
                    exc_info=True)
            else:
                try:
                    shutil.rmtree(self.image_rootfs_path)
                except Exception as e:
                    logger.warning(
                        "Failed to remove= %s - Error: %s" % (
                            self.image_rootfs_path, str(e)),
                        exc_info=True
                    )
            # retry once more
            try:
                os.makedirs(self.image_rootfs_path)
            except OSError as error:
                logger.fatal(str(error), exc_info=True)
                # fail! and return
                return False

        logger.info(
            "Mounting rootfs %s on %s" % (
                self.image_id, self.image_rootfs_path))
        self.mount_object.mount()
        logger.info("Successfully mounted image's rootfs")
        return True

    def unmount_image(self):
        """
        Unmount image using the Atomic mount object
        """
        logger.info("Unmounting image's rootfs from %s"
                    % self.mount_object.mountpoint)
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
            logger.warning(
                "Error removing image rootfs path. %s" % str(error),
                exc_info=True
            )
        logger.info(
            "Removing the image %s" % self.image_under_test)
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

        logger.info("Executing atomic scan:  %s" % " ".join(cmd))
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
            logger.info("Result file: %s" % output_json_file)

            if os.path.exists(output_json_file):
                json_data = json.loads(open(output_json_file).read())
                self.clean_scanner_result(output_json_file)
            else:
                logger.fatal(
                    "No scan results found at %s" % output_json_file)
                return False, json_data
        else:
            logger.warning(
                "Failed to get the results from atomic CLI. Error:%s" % err
            )
            return False, json_data

        self.unmount_image()
        shutil.rmtree(self.image_rootfs_path, ignore_errors=True)
        logger.info(
            "Finished executing scanner: %s" % self.scanner_name)
        return True, self.process_output(json_data)

    def clean_scanner_result(self, path):
        """
        Clean the scanner  results from /var/lib/atomic directory
        """
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Failed to remove %s" % path)
            logger.warning("Error: %s" % str(e))

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


class ContainerCapabilities(Scanner):

    def __init__(self):
        self.scanner_name = "container-capabilities-scanner"
        self.full_scanner_name = \
            "registry.centos.org/pipeline-images/" \
            "container-capabilities-scanner"
        self.scan_types = ["check-capabilities"]

    def run(self, image_under_test):
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

        scan_results = super(ContainerCapabilities, self).run(scan_cmd)

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


bs = beanstalkc.Connection(host=BEANSTALKD_HOST)
bs.watch("start_scan")


while True:
    try:
        job = bs.reserve()
        job_info = json.loads(job.body)

        debug_logs_file = os.path.join(
            job_info["logs_dir"], "service_debug.log")
        dfh = config.DynamicFileHandler(logger, debug_logs_file)

        logger.info('Got job: %s' % job_info)
        scan_runner_obj = ScannerRunner(job_info)
        status, scanners_data = scan_runner_obj.run()
        if not status:
            logger.critical(
                "Failed to run scanners on image under test, moving on!"
            )
        else:
            logger.info(str(scanners_data))
        # if weekly scan, push the job for notification
        if job_info.get("weekly"):
            bs.use("master_tube")
            bs.put(json.dumps(job_info))
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            next_job = job_info
            # change the action
            next_job["action"] = "start_delivery"
            # Remove the msg and logs from the job_info as they are not
            # needed now
            next_job.pop("msg", None)
            next_job.pop("logs", None)
            next_job.pop("scan_results", None)
            # Put the job details on central tube
            bs.use("master_tube")
            job_id = bs.put(json.dumps(next_job))
            logger.info(
                "Put job for delivery on master tube with id = %s" % job_id
            )
    except Exception as e:
        logger.fatal(str(e), exc_info=True)
        job_info["action"] = "start_delivery"
        bs.use("master_tube")
        bs.put(json.dumps(job_info))
    finally:
        logger.info("Job moved from scan phase.")
        job.delete()

        # remove per file build log handler from logger
        if 'dfh' in locals():
            dfh.remove()
