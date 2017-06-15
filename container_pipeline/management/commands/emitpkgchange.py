from django.core.management.base import BaseCommand  # CommandError
import logging
import fedmsg

from container_pipeline.tracking.lib import get_navr_from_pkg_name

logger = logging.getLogger('tracking')


class Command(BaseCommand):
    help = 'Emit package change for test'
    args = '[<pkg_name1>,<pkg_name2> upstream_id]'

    def handle(self, *args, **options):
        argc = len(args)
        if argc > 0:
            upstream = args[1] if argc > 1 else None
            for arg in args[0].split(','):
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
