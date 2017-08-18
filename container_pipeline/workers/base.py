import json
import logging
import os
import time

from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue
from container_pipeline.lib.log import DynamicFileHandler


class BaseWorker(object):
    """Base class for pipeline workers"""
    NAME = ''

    def __init__(self, logger=None, sub=None, pub=None):
        self.logger = logger or logging.getLogger('console')
        self.queue = JobQueue(host=settings.BEANSTALKD_HOST,
                              port=settings.BEANSTALKD_PORT,
                              sub=sub, pub=pub, logger=self.logger)
        if not self.NAME:
            raise Exception('Define name for your worker class!')

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
        self.logger.info('Writing logs to NFS share')
        # to take care if the logs directory is not created
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        try:
            with open(destination, "w") as fin:
                fin.write(logs)
        except IOError as e:
            self.logger.error("Failed writing logs to {}: {}"
                              .format(destination, e))

    def run(self):
        """Run worker"""
        self.logger.info('{} running...'.format(self.NAME))

        while True:
            job_obj = None
            try:
                job_obj = self.queue.get()
                job = json.loads(job_obj.body)

                # Skip retrying a job if it's too early and push it back to
                # queue. This will allow us to introduce some delays between
                # job retries
                if job.get('retry') is True and (
                        time.time() - job.get('last_run_timestamp', 0) <
                        job.get('retry_delay', 0)):
                    time.sleep(10)
                    self.queue.put(json.dumps(job), 'master_tube')
                else:
                    debug_logs_file = os.path.join(
                        job['logs_dir'], settings.SERVICE_LOGFILE)
                    # Run dfh.clean() to clean log files if no error is
                    # encountered in post delivering build report mails to user
                    dfh = DynamicFileHandler(self.logger, debug_logs_file)
                    self.logger.info('Got job: {}'.format(job))
                    try:
                        self.handle_job(job)
                    except Exception as e:
                        self.logger.error(
                            'Error in handling job: {}\nJob details: {}'
                            .format(e, job), extra={'locals': locals()},
                            exc_info=True)
                    dfh.remove()
            except Exception as e:
                self.logger.critical(
                    'Unexpected error when processing job: {}'.format(e),
                    exc_info=True)
            finally:
                if job_obj:
                    self.queue.delete(job_obj)
