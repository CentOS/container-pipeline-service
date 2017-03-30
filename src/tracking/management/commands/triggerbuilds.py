import time
import logging

from django.core.management.base import BaseCommand  # CommandError
from django.utils import timezone
from django.conf import settings

from tracking.models import ContainerImage, Package

logger = logging.getLogger('cccp')


class Command(BaseCommand):
    help = 'Trigger image builds due for building'

    def handle(self, *args, **options):
        logger.info(
            'Triggering image builds...')
        while True:
            try:
                last_updated = Package.objects.all().order_by(
                    '-last_updated')[0].last_updated
            except IndexError:
                continue
            if (timezone.now() - last_updated).seconds < (
                    settings.CONTAINER_BUILD_TRIGGER_DELAY):
                logger.info('Waiting for package change burst to complete')
                time.sleep(settings.CONTAINER_BUILD_TRIGGER_DELAY)
                continue
            to_build = set()
            qs = ContainerImage.objects.filter(to_build=True)
            for container in qs:
                parents_in_to_build = qs.filter(
                    id__in=[item.id for item in container.parents.all()])
                if parents_in_to_build:
                    try:
                        to_build.remove(container)
                    except KeyError:
                        pass
                    container.to_build = False
                    container.save()
                    logger.debug('Removed image: %s from build queue'
                                 % container)
                    logger.debug('Parents in build queue: %s' %
                                 parents_in_to_build)
                else:
                    to_build.add(container)
            for c in to_build:
                logger.info('Triggering image build for %s' % c)
                c.trigger_build()
                c.to_build = False
                c.save()
            time.sleep(settings.CONTAINER_BUILD_TRIGGER_DELAY)