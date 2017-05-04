#!/usr/bin/env python

import json
import logging


import beanstalkc
import config


config.load_logger()
logger = logging.getLogger("dispatcher")

bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.watch("master_tube")

logger.info("Starting dispatcher")

while True:
    job = bs.reserve()
    job_details = json.loads(job.body)
    logger.info('Got job: %s' % job_details)

    logger.info("Retrieving job action")
    action = str(job_details['action'])

    if action == "start_build":
        bs.use("start_build")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to build tube")

    elif action == "start_test":
        bs.use("start_test")
        bs.put(json.dumps(job_details))
        logger.info("==> Job moved to build tube")

    elif action == "start_scan":
        bs.use("start_scan")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to test tube")

    elif action == "start_delivery":
        bs.use("start_delivery")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to delivery tube")

    elif action == "notify_user":
        bs.use("notify_user")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to notify tube")

    elif action == "report_scan_results":
        bs.use("report_scan_results")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to report scan results tube")

    elif action == "start_linter":
        bs.use("start_linter")
        bs.put(json.dumps(job_details))
        logger.info("Job moved to linter tube")

    logger.debug("Deleting job: %s" % job_details)
    job.delete()
