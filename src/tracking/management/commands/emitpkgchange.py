from django.core.management.base import BaseCommand  # CommandError
import logging
import fedmsg

from tracking.lib import get_navr_from_pkg_name

logger = logging.getLogger('cccp')


class Command(BaseCommand):
    help = 'Emit package change for test'
    args = '[<pkg_name1> <pkg_name2> ...]'

    def handle(self, *args, **options):
        if args:
            for arg in args:
                try:
                    n, a, v, r = get_navr_from_pkg_name(arg)
                except:
                    logger.error('Unable to parse package name: %s' % arg)
                    continue
                logger.debug('Emitting package.added message for: %s' % arg)
                fedmsg.publish(topic='package.added',
                               modname='container_pipeline',
                               msg={
                                   'upstream': {},
                                   'package': {
                                       'name': n,
                                       'arch': a,
                                       'version': v,
                                       'release': r,
                                       'epoch': '0'
                                   }
                               })
