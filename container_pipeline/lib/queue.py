import logging
import time

from container_pipeline.vendors import beanstalkc


def retry(delay=30):
    """Decorator to handle beanstalkd outage and recover"""
    def _retry(func):
        def wrapper(*args, **kwargs):
            error_logged = False
            while True:
                try:
                    return func(*args, **kwargs)
                except beanstalkc.SocketError:
                    obj = args[0]
                    if not error_logged:
                        obj.logger.error('Lost connection to beanstalkd')
                        error_logged = True
                    time.sleep(delay)
                    if func != obj._initialize:
                        obj._initialize()
        return wrapper
    return _retry


class JobQueue:
    """Abstraction layer around job queue"""
    def __init__(self, host, port, sub, pub=None, logger=None):
        self.host = host
        self.port = port
        self.sub = sub
        self.pub = pub or self.sub
        self.logger = logger or logging.getLogger('console')
        self._initialize()

    @retry()
    def get(self):
        """Get job from subscribed tube"""
        self.logger.debug('Waiting to get data from tube: {}...'
                          .format(self.sub))
        return self._conn.reserve()

    @retry()
    def put(self, data, tube=None):
        """Put job to tube"""
        if tube:
            self._conn.use(tube)
        self.logger.debug('Put data to tube {}: {}'.format(tube, data))
        self._conn.put(data)
        self._conn.use(self.sub)

    @retry()
    def delete(self, job):
        """Delete job from queue"""
        job.delete()

    @retry()
    def _initialize(self):
        """Initialize connection to queue backend"""
        self._conn = beanstalkc.Connection(host=self.host, port=self.port)
        self._conn.watch(self.sub)
        self._conn.use(self.pub)
        self.logger.info('Connection to beanstalkd initialized')
