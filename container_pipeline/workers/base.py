import json
import logging
import os

from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue


class BaseWorker(object):
    """Base class for pipeline workers"""

    def __init__(self, logger=None, sub=None, pub=None):
        self.logger = logger or logging.getLogger('console')
        self.queue = JobQueue(host=settings.BEANSTALKD_HOST,
                              port=settings.BEANSTALKD_PORT,
                              sub=sub, pub=pub, logger=self.logger)

    def handle_job(self, job):
        """
        This method is called to process job data from task queue.
        """
        raise NotImplementedError

    def notify_build_failure(self, namespace, notify_email, build_logs_file,
                             project_name, job_name, test_tag):
        """This method queues user notifications for build failure, to be
        processed by the mail service worker"""
        data = {}
        data['action'] = 'notify_user'
        data['namespace'] = namespace
        data['build_status'] = False
        data['notify_email'] = notify_email
        data['build_logs_file'] = build_logs_file
        data['project_name'] = project_name
        data['job_name'] = job_name
        data['TEST_TAG'] = test_tag
        self.queue.put(json.dumps(data), 'master_tube')
        self.logger.debug('Notify build failure: {}'.format(data))

    def export_build_logs(self, logs, destination):
        """"Write logs in given destination"""
        self.logger.debug('Writing build logs to NFS share')
        # to take care if the logs directory is not created
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        try:
            with open(destination, "w") as fin:
                fin.write(logs)
        except IOError as e:
            self.logger.critical("Failed writing logs to {}"
                                 .format(destination))
            self.logger.critical(str(e))

    def run(self):
        """Run worker"""
        while True:
            job_obj = self.queue.get()
            job = json.loads(job_obj.body)
            self.logger.info('Got job: {}'.format(job))
            try:
                self.handle_job(job)
            except Exception as e:
                self.logger.error(
                    'Error in handling job: {}\nJob details: {}'.format(
                        e, job), extra={'locals': locals()}, exc_info=True)
            self.queue.delete(job_obj)
