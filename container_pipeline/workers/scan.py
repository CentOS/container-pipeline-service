#!/usr/bin/python
"""Scan Base Worker."""

import json
import logging
import os

from container_pipeline.lib import dj  # noqa
from django.utils import timezone

import container_pipeline.lib.log as log
from container_pipeline.workers.base import BaseWorker
from container_pipeline.scanners.runner import ScannerRunner
from container_pipeline.lib import settings

from container_pipeline.models import Build, BuildPhase


class ScanWorker(BaseWorker):
    """Scan Base worker."""
    NAME = 'Scanner worker'

    def __init__(self, logger=None,sub=None, pub=None):
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
                "Failed to run scanners on image under test, moving on!",
                extra=self.job
            )
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
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            # change the action
            scanners_data["action"] = "start_delivery"
            # Put the job details on central tube
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.init_next_phase_data('delivery')
            self.logger.debug("Put job for delivery on master tube")

        # remove per file build log handler from logger
        if 'dfh' in locals():
            dfh.remove()


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("scan-worker")
    ScanWorker(logger, sub='start_scan', pub='failed_scan').run()
