import json
import logging
import os

from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue
from container_pipeline.lib.log import DynamicFileHandler


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

    def notify(self, data):
        """
        This method queues user notifications to be processed by the
        mail service worker. Customize as needed.
        """
        self.queue.put(json.dumps(data), 'master_tube')

    def export_logs(self, logs, destination):
        """"Write logs in given destination"""
        self.logger.info('Writing build logs to NFS share')
        # to take care if the logs directory is not created
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        try:
            with open(destination, "w") as fin:
                fin.write(logs)
        except IOError as e:
            self.logger.critical("Failed writing logs to {}"
                                 .format(destination))
            self.logger.error(str(e))

    def run(self):
        """Run worker"""
        while True:
            job_obj = self.queue.get()
            job = json.loads(job_obj.body)
            debug_logs_file = os.path.join(
                job['logs_dir'], settings.SERVICE_LOGFILE)
            # Run dfh.clean() to clean log files if no error is encountered in
            # post delivering build report mails to user
            dfh = DynamicFileHandler(self.logger, debug_logs_file)
            self.logger.info('Got job: {}'.format(job))
            try:
                self.handle_job(job)
            except Exception as e:
                self.logger.error(
                    'Error in handling job: {}\nJob details: {}'.format(
                        e, job), extra={'locals': locals()}, exc_info=True)
            dfh.remove()
            self.queue.delete(job_obj)
