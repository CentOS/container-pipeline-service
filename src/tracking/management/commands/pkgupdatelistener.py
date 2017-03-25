from django.core.management.base import BaseCommand

import fedmsg

from tracking.models import Package


class Command(BaseCommand):

    def handle(self, *args, **options):
        for name, endpoint, topic, msg in fedmsg.tail_messages():
            print topic, msg
            if topic.endswith('package.modified') or \
                    topic.endswith('package.removed') or \
                    topic.endswith('package.added'):
                pkg = msg['msg']['package']
                for package in Package.objects.filter(
                        name=pkg['name'], arch=pkg['arch']):
                    if package.version != pkg['version'] or \
                            package.release != pkg['release']:
                        package.images.update(to_build=True)
