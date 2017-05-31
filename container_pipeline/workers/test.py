#!/usr/bin/python

import hashlib
import json
import logging
import os

from container_pipeline.utils import Build, get_job_name
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.workers.base import BaseWorker


class TestWorker(BaseWorker):
    """Test Worker"""

    def __init__(self, logger=None, sub=None, pub=None):
        super(TestWorker, self).__init__(logger=logger, sub=sub, pub=pub)
        self.openshift = Openshift(logger=self.logger)

    def test(self, job):
        """Runs openshift test job"""
        namespace = get_job_name(job)
        project = hashlib.sha224(namespace).hexdigest()

        try:
            self.openshift.login()
            build_id = self.openshift.build(project, 'test')
            if not build_id:
                return False
        except OpenshiftError as e:
            logger.error(e)
            return False

    def handle_test_success(self, job):
        """Handle build success for job"""
        self.logger.debug("Test is successful going for next job")

    def handle_test_failure(self, job):
        """Handle build failure for job"""
        self.queue.put(json.dumps(job))
        self.logger.info(
            "Test is not successful putting it to failed build tube")
        appid = job['appid']
        jobid = job['jobid']
        desired_tag = job['desired_tag']
        project = appid + "/" + jobid + ":" + desired_tag
        test_logs_file = os.path.join(job['logs_dir'], 'test_logs.txt')
        self.notify_build_failure(
            get_job_name(job), job['notify_email'], test_logs_file,
            project, job['jobid'], job['TEST_TAG'])

    def handle_job(self, job):
        """This runs the user defined tests on the container."""
        self.logger.info('Starting build for job: {}'.format(job))
        success = self.test(job)

        if success:
            self.handle_test_success(job)
        else:
            self.handle_test_failure(job)


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('test-worker')
    worker = TestWorker(logger, sub='start_test', pub='test_failed')
    worker.run()
