from django.core.management.base import BaseCommand

import fedmsg
import logging

from tracking.models import Package

logger = logging.getLogger('cccp')


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Listening for package updates...')
        for name, endpoint, topic, msg in fedmsg.tail_messages():
            if topic.endswith('package.modified') or \
                    topic.endswith('package.removed') or \
                    topic.endswith('package.added'):
                pkg = msg['msg']['package']
                for package in Package.objects.filter(
                        name=pkg['name'], arch=pkg['arch']):
                    if package.version != pkg['version'] or \
                            package.release != pkg['release']:
                        logger.info('Package changed: %s %s' % (pkg, package))
                        package.images.update(to_build=True)
                        logger.info('Images marked for build: %s' %
                                    package.images.all())
