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



if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('test-worker')
    worker = TestWorker(logger, sub='start_test', pub='failed_build')
    worker.run()
