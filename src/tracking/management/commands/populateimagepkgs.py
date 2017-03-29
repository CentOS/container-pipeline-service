from django.core.management.base import BaseCommand  # CommandError
import logging

from tracking.models import ContainerImage, Package
from tracking.lib import get_navr_from_pkg_name

logger = logging.getLogger('cccp')


class Command(BaseCommand):
    help = 'Populate RPM packages data for container images'
    args = '[<image_name1> <image_name2> ...]'

    def handle(self, *args, **options):
        logger.info('Populating packages data for images')
        filters = {}
        if args:
            filters['name__in'] = args
        for container in ContainerImage.objects.filter(**filters):
            logger.debug('Populating packages for image: %s' % container)
            container.pull()
            output = container.run('rpm -qa')
            packages = []
            for line in output.splitlines():
                if not line:
                    continue
                name, arch, version, release = get_navr_from_pkg_name(line)
                p, created = Package.objects.get_or_create(
                    name=name, version=version, release=release, arch=arch)
                packages.append(p)
            container.packages.add(*packages)
        logger.info('Populated packages data for images')
