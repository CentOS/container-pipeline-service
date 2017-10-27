#!/usr/bin/env python
import json
import logging
import os
import time

from container_pipeline.lib import dj  # noqa
from django.utils import timezone

from container_pipeline.lib import settings
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.utils import Build as BuildTracker, get_cause_of_build
from container_pipeline.workers.base import BaseWorker


class BuildWorker(BaseWorker):
    """Build worker"""
    NAME = 'BUILD WORKER'

    def __init__(self, logger=None, sub=None, pub=None):
        super(BuildWorker, self).__init__(logger, sub, pub)
        self.build_phase_name = "build"
        self.openshift = Openshift(logger=self.logger)

    def handle_job(self, job):
        """
        This checks if parents for the current project are being built.
        If any parent build is in progress, it pushes the job back to the
        queue to be processed later. Else, it goes ahead with running
        build for the job.
        """
        self.job = job

        self.job["cause_of_build"] = get_cause_of_build(
            os.environ.get('JENKINS_MASTER'),
            self.job["job_name"],
            self.job["jenkins_build_number"]
        )

        parent_build_running = False
        parents = self.job.get('depends_on', '').split(',')
        parents_in_build = []

        # Reset retry params
        self.job['retry'] = None
        self.job['retry_delay'] = None
        self.job['last_run_timestamp'] = None

        for parent in parents:
            is_build_running = BuildTracker(parent, logger=self.logger).is_running()
            if is_build_running:
                parents_in_build.append(parent)
            parent_build_running = parent_build_running or \
                is_build_running

        if parent_build_running:
            self.logger.info('Parents in build: {}, pushing job: {} back '
                             'to queue'.format(parents_in_build, self.job))
            # Retry delay in seconds
            self.job['retry'] = True
            self.job['retry_delay'] = settings.BUILD_RETRY_DELAY
            self.job['last_run_timestamp'] = time.time()
            self.queue.put(json.dumps(self.job), 'master_tube')
        else:
            self.logger.info('Starting build for job: {}'.format(self.job))
            success = self.build()
            if success:
                self.job["build_status"] = True
                self.handle_build_success()
            else:
                self.job["build_status"] = False
                self.handle_build_failure()

    def build(self):
        """Run Openshift build for job"""
        namespace = self.job["namespace"]
        # project_name = self.job["project_name"]
        project_hash_key = self.job["project_hash_key"]

        try:
            self.openshift.login()
            build_id = self.openshift.build(project_hash_key, 'build')
            if not build_id:
                return False
        except OpenshiftError as e:
            self.logger.error(e)
            return False

        BuildTracker(namespace).start()
        build_status = self.openshift.wait_for_build_status(
            project_hash_key, build_id, 'Complete')
        logs = self.openshift.get_build_logs(project_hash_key, build_id)
        build_logs_file = os.path.join(self.job['logs_dir'], 'build_logs.txt')
        self.export_logs(logs, build_logs_file)
        return build_status

    def handle_build_success(self):
        """Handle build success for job."""
        self.job['action'] = 'start_test'
        self.queue.put(json.dumps(self.job), 'master_tube')
        self.logger.debug("Build is successful going for next job")

    def handle_build_failure(self):
        """Handle build failure for job"""
        self.job['action'] = "notify_user"
        self.queue.put(json.dumps(self.job), 'master_tube')
        self.logger.warning(
            "Build is not successful. Notifying the user.")
        # data = {
        #     'action': 'notify_user',
        #     'namespace': self.job["namespace"],
        #     'build_status': False,
        #     'notify_email': self.job['notify_email'],
        #     'build_logs_file': os.path.join(
        #         self.job['logs_dir'], 'build_logs.txt'),
        #     'logs_dir': self.job['logs_dir'],
        #     'project_name': self.job['project_name'],
        #     'job_name': self.job['job_name'],
        #     'test_tag': self.job['test_tag']}


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('build-worker')
    worker = BuildWorker(logger, sub='start_build', pub='failed_build')
    worker.run()
