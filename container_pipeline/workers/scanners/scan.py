#!/usr/bin/python
"""Scan Base Worker."""

import json
import logging
import os

import container_pipeline.lib.log as log
from container_pipeline.workers.base import BaseWorker
from container_pipeline.workers.scanners.runner import ScannerRunner


class ScanWorker(BaseWorker):
    """Scan Base worker."""

    def handle_job(self, job):
        """
        Handle jobs in scan tube.

        This scans the images for the job requests in start_scan tube.
        this calls the ScannerRunner for performing the scan work
        """
        debug_logs_file = os.path.join(
            job["logs_dir"], "service_debug.log")
        dfh = log.DynamicFileHandler(logger, debug_logs_file)

        self.logger.info('Got job: {}'.format(job))
        scan_runner_obj = ScannerRunner(job)
        status, scanners_data = scan_runner_obj.scan()
        if not status:
            logger.critical(
                "Failed to run scanners on image under test, moving on!"
            )
        else:
            self.logger.info(str(scanners_data))

        # Remove the msg and logs from the job_info as they are not
        # needed now
        scanners_data.pop("msg", None)
        scanners_data.pop("logs", None)
        scanners_data.pop("scan_results", None)

        # if weekly scan, push the job for notification
        if job.get("weekly"):
            scanners_data["action"] = "notify_user"
            self.queue.put(json.dumps(scanners_data), 'master_tube')
        else:
            # now scanning is complete, relay job for delivery
            # all other details about job stays same
            # change the action
            scanners_data["action"] = "start_delivery"
            # Put the job details on central tube
            self.queue.put(json.dumps(scanners_data), 'master_tube')
            self.logger.info("Put job for delivery on master tube")

        # remove per file build log handler from logger
        if 'dfh' in locals():
            dfh.remove()


if __name__ == '__main__':

    log.load_logger()
    logger = logging.getLogger("scan-worker")
    ScanWorker(logger, sub='start_scan', pub='failed_scan').run()
