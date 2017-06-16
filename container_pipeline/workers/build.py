#!/usr/bin/env python
import json
import logging
import os

from container_pipeline.utils import Build, get_job_name, get_project_name, \
    get_job_hash
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.workers.base import BaseWorker


class BuildWorker(BaseWorker):
    """Build worker"""

    def __init__(self, logger=None, sub=None, pub=None):
        super(BuildWorker, self).__init__(logger, sub, pub)
        self.openshift = Openshift(logger=self.logger)

    def handle_job(self, job):
        """
        This checks if parents for the current project are being built.
        If any parent build is in progress, it pushes the job back to the
        queue to be processed later. Else, it goes ahead with running
        build for the job.
        """
        parent_build_running = False
        parents = job.get('depends_on', '').split(',')
        parents_in_build = []
        for parent in parents:
            is_build_running = Build(parent).is_running()
            if is_build_running:
                parents_in_build.append(parent)
            parent_build_running = parent_build_running or \
                is_build_running

        if parent_build_running:
            self.logger.info('Parents in build: {}, pushing job: {} back '
                             'to queue'.format(parents_in_build, job))
            self.queue.put(json.dumps(job), 'master_tube')
        else:
            self.logger.info('Starting build for job: {}'.format(job))
            success = self.build(job)
            if success:
                self.handle_build_success(job)
            else:
                self.handle_build_failure(job)

    def build(self, job):
        """Run Openshift build for job"""
        namespace = get_job_name(job)
        project = get_job_hash(namespace)

        try:
            self.openshift.login()
            build_id = self.openshift.build(project, 'build')
            if not build_id:
                return False
        except OpenshiftError as e:
            logger.error(e)
            return False

        Build(namespace).start()
        build_status = self.openshift.wait_for_build_status(
            project, build_id, 'Complete')
        logs = self.openshift.get_build_logs(project, build_id)
        build_logs_file = os.path.join(job['logs_dir'], 'build_logs.txt')
        self.export_logs(logs, build_logs_file)
        return build_status

    def handle_build_success(self, job):
        """Handle build success for job"""
        self.logger.debug("Build is successful going for next job")

    def handle_build_failure(self, job):
        """Handle build failure for job"""
        self.queue.put(json.dumps(job))
        self.logger.info(
            "Build is not successful putting it to failed build tube")
        data = {
            'action': 'notify_user',
            'namespace': get_job_name(job),
            'build_status': False,
            'notify_email': job['notify_email'],
            'build_logs_file': os.path.join(
                job['logs_dir'], 'build_logs.txt'),
            'project_name': get_project_name(job),
            'job_name': job['jobid'],
            'TEST_TAG': job['TEST_TAG']}
        self.logger.debug('Notify build failure: {}'.format(data))
        self.notify(data)


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('build-worker')
    worker = BuildWorker(logger, sub='start_build', pub='failed_build')
    worker.run()
