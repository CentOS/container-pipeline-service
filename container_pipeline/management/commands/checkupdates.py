from django.core.management.base import BaseCommand  # CommandError
from django.conf import settings
import logging
import json

from container_pipeline.models.tracking import RepoInfo
from container_pipeline.tracking.lib.repo import process_upstream, publish

logger = logging.getLogger('tracking')


class Command(BaseCommand):
    help = 'Check for repo updates'

    def handle(self, *args, **options):
        logger.info('Checking for upstream updates')
        for repoinfo in RepoInfo.objects.all():
            try:
                data = {
                    'baseurls': json.loads(repoinfo.baseurls),
                    'basearch': repoinfo.basearch,
                }
                added, modified, removed = process_upstream(
                    repoinfo.id, data, settings.UPSTREAM_PACKAGE_CACHE)
                publish(added, modified, removed, repoinfo.id)
            except Exception as e:
                logger.error(
                    'Error in fetching update info for %s: %s' % (
                        repoinfo, e), exc_info=True)
