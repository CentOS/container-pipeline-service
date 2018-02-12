#!/usr/bin/python

"""
moduleauthor: The Container Pipeline Service Team

This module contains the worker that handles the scanning on the
Container Pipeline Service
"""

from container_pipeline.lib import dj  # noqa
from container_pipeline.lib import settings
from container_pipeline.lib.command import run_cmd_out_err
import container_pipeline.lib.log as log
from container_pipeline.workers.base import BaseWorker
from container_pipeline.scanners.runner import ScannerRunner
from django.utils import timezone
import json
import logging
import os


class ScanWorker(BaseWorker):
    """Scan Base worker."""
    NAME = 'Scanner worker'

    def __init__(self, logger=None, sub=None, pub=None):
        super(ScanWorker, self).__init__(logger=logger, sub=sub, pub=pub)
        self.build_phase_name = 'scan'

    def handle_job(self, job):
        """
        Handle jobs in scan tube.

        This scans the images for the job requests in start_scan tube.
        this calls the ScannerRunner for performing the scan work
        """
        self.job = job
        self.setup_data()
        self.set_buildphase_data(
            build_phase_status='processing',
            build_phase_start_time=timezone.now()
        )

        debug_logs_file = os.path.join(
            self.job["logs_dir"], settings.SERVICE_LOGFILE)
        dfh = log.DynamicFileHandler(self.logger, debug_logs_file)

        scan_runner_obj = ScannerRunner(self.job)
        status, scanners_data = scan_runner_obj.scan()
        if not status:
            self.logger.warning(
                "Failed to run scanners on image under test, moving on!")
            self.logger.warning("Job data %s", str(self.job))

            self.set_buildphase_data(
                build_phase_status='complete',
                build_phase_end_time=timezone.now()
            )
        else:
            self.set_buildphase_data(
                build_phase_status='failed',
                build_phase_end_time=timezone.now()
            )
            self.logger.debug(str(scanners_data))

        # Remove the msg and logs from the job_info as they are not
        # needed now
        scanners_data.pop("msg", None)
        scanners_data.pop("logs", None)
        scanners_data.pop("scan_results", None)

        # if weekly scan, push the job for notification
        if self.job.get("weekly"):
            scanners_data["action"] = "notify_user"
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.init_next_phase_data('delivery')
            self.logger.debug(
                str.format(
                    "Weekly scan for {project} is complete.",
                    project=self.job.get("namespace")
                )
            )
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            # change the action
            scanners_data["action"] = "start_delivery"
            # Put the job details on central tube
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.init_next_phase_data('delivery')
            self.logger.debug("Put job for delivery on master tube")

        # run the image and volume cleanup
        self.clean_up()

        # remove per file build log handler from logger
        if 'dfh' in locals():
            dfh.remove()

    def clean_up(self):
        """
        Clean up the system after scan is done.
        This cleans up any unused/dangling images and volumes.
        This is using `docker image prune -f` and `docker volume prune -f`
        commands under the hood. The `-f` option will help avoid the prompt
        for confirmation.
        """
        command = ["docker", "image", "prune", "-f"]
        self.logger.debug("Removing unused/dangling images..")
        try:
            out, error = run_cmd_out_err(command)
        except Exception as e:
            self.logger.critical("Failing to remove dangling images.")
            self.logger.critical("Error %s:%s", str(e), str(error))
        else:
            self.logger.debug("Cleaned unsued images: %s", str(out))

        command = ["docker", "volume", "prune", "-f"]
        self.logger.debug("Removing unused/dangling volumes..")
        try:
            out, error = run_cmd_out_err(command)
        except Exception as e:
            self.logger.critical("Failing to remove dangling volume.")
            self.logger.critical("Error %s:%s", str(e), str(error))
        else:
            self.logger.debug("Cleaned unsued volumes: %s", str(out))


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("scan-worker")
    ScanWorker(logger, sub='start_scan', pub='failed_scan').run()
