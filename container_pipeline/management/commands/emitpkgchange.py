from django.core.management.base import BaseCommand  # CommandError
import logging
import fedmsg

from container_pipeline.tracking.lib import get_navr_from_pkg_name

logger = logging.getLogger('tracking')


class Command(BaseCommand):
    help = 'Emit package change for test'
    args = '[<pkg_name1>,<pkg_name2> upstream_id]'

    def add_arguments(self, parser):
        # get all the args in arguments
        parser.add_argument('arguments', nargs='+', type=str)

    def handle(self, *args, **options):
        arguments = options["arguments"]

        # <pkg_name1>,<pkg_name2>
        packages = arguments[0]

        # to check if upstream is given or not
        argc = len(arguments)
        upstream = arguments[1] if argc > 1 else None

        for arg in packages.split(','):
            try:
                n, a, v, r = get_navr_from_pkg_name(arg)
            except:
                logger.error('Unable to parse package name: %s' % arg)
                continue
            logger.debug('Emitting package.added message for: %s' % arg)
            fedmsg.publish(topic='package.added',
                           modname='container_pipeline',
                           msg={
                               'upstream': upstream,
                               'package': {
                                   'name': n,
                                   'arch': a,
                                   'version': v,
                                   'release': r,
                                   'epoch': '0'
                               }
                           })
