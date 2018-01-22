from django.core.management.base import BaseCommand  # CommandError
from container_pipeline.models import ContainerImage
import logging

from jenkinsbuilder import cccp_index_reader as cir


logger = logging.getLogger('tracking')


class Command(BaseCommand):
    help = 'Delete stale images from database'

    def add_arguments(self, parser):
        parser.add_argument('indexd_path')

    def handle(self, *args, **options):
        logger.info("Checking for stale projects")
        indexd_path = options['indexd_path']

        old_projects = cir.get_old_project_list()
        new_projects = cir.get_new_project_list(indexd_path)

        stale_projects = cir.find_stale_projects(old_projects, new_projects)
        logger.info("List of stale projects: %s ", str(stale_projects))

        for project in stale_projects:
            try:
                container_image = ContainerImage.objects.get(name=project)
            except Exception as e:
                logger.critical(
                    "Error querying database ContainerImage "
                    "table with project name {}.".format(project))
                logger.error(str(e))
            else:
                if not container_image:
                    logger.warning(
                        "{0} project entry mapping container image does "
                        "not exist in ContainerImage table".format(project))
                else:
                    try:
                        container_image.delete()
                    except Exception as e:
                        logger.error("Error deleting container {0} "
                                     "for project {1}".format(
                                         container_image.name, project))
                        logger.error(str(e))
                    else:
                        logger.info(
                            "Deleted entry {0} for project {1} from "
                            "ContainerImage table.".format(
                                container_image.name, project))
