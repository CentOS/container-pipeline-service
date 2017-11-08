from django.core.management.base import BaseCommand  # CommandError
from container_pipeline.models.tracking import ContainerImage
import logging

from jenkinsbuilder import cccp_index_reader as cir


logger = logging.getLogger('tracking')


class Command(BaseCommand):
    help = 'Delete stale images from database'

    def handle(self, *args, **options):
        logger.info("Checking for stale projects")
        indexd_path = args[0]

        old_projects = cir.get_old_project_list()
        new_projects = cir.get_new_project_list(indexd_path)

        stale_projects = cir.find_stale_projects(old_projects, new_projects)

        for project in stale_projects:
            try:
                container_image = ContainerImage.objects.get(name=project)
                container_image.delete()
            except Exception as e:
                logger.critical("Error deleting image {}".format(container_image))
                logger.error(e)
