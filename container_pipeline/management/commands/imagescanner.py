from django.core.management.base import BaseCommand  # CommandError
import logging
import json
import sys
from django.utils import timezone
from django.conf import settings

from container_pipeline.lib.queue import JobQueue

from container_pipeline.models.tracking import Package,\
    RepoInfo
from container_pipeline.models import ContainerImage
from container_pipeline.tracking.lib import get_navr_from_pkg_name

logger = logging.getLogger('tracking')

# this is a dictionary for URLs for alternate repos like EPEL, remi-repos, etc.
# which contain mirrorlist that doesn't yield repomd.xml or repodata dir from
# the URL itself
alt_repos = {
    "epel": "https://mirrors.fedoraproject.org/mirrorlist?repo=epel-7&arch=x86_64",
    "remi-safe": "http://rpms.remirepo.net/enterprise/7/safe/x86_64/"
}


def populate_packages(container):
    """Populate RPM packages installed data from container image"""
    logger.debug('Populating packages for image: %s' % container)
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


def populate_upstreams(container):
    """Populate enabled repos data from container image"""
    logger.debug('Populating upstream data for image: %s' % container)
    output = container.run(
        'python -c "import yum, json; yb = yum.YumBase(); '
        'print json.dumps([(r.id, r.mirrorlist, r.baseurl) '
        'for r in yb.repos.listEnabled()])"')
    data = json.loads(output.splitlines()[-1])
    urls = set()
    for item in data:
        if item[0] in alt_repos:
            urls.add(alt_repos[item[0]])
            continue
        urls.add(item[1])
        for url in item[2]:
            urls.add(url)

    if None in urls:
        urls.remove(None)

    output = container.run(
        'python -c "import yum, json; yb = yum.YumBase(); '
        'print json.dumps(yb.conf.yumvar)"')
    data = json.loads(output.splitlines()[-1])
    basearch = data['basearch']
    releasever = data['releasever']
    infra = data['infra']
    repoinfo, created = RepoInfo.objects.get_or_create(
        baseurls=json.dumps(list(urls)), defaults={
            'releasever': releasever, 'basearch': basearch,
            'infra': infra
        })
    container.repoinfo = repoinfo
    container.save()


def scan_image(image):
    """Scan the given container image"""
    image.pull()
    populate_packages(image)
    populate_upstreams(image)
    image.scanned = True
    image.last_scanned = timezone.now()
    image.save()
    image.remove()


class Command(BaseCommand):
    help = 'Scan container images'
    args = '[onetime <image_name1> <image_name2> ...]'

    def handle(self, *args, **options):
        try:
            logger.debug('Scanning not already scanned images')
            filters = {}
            if args:
                if args[0] != 'onetime':
                    filters['name__in'] = args
                filters['scanned'] = False
            for image in ContainerImage.objects.filter(**filters):
                try:
                    scan_image(image)
                    logger.info('Scanned new image: {}'.format(image))
                except Exception as e:
                    logger.error('Image scan error for %s: %s' % (image, e),
                                 exc_info=True)
            logger.info('Scanned not already scanned images')

            if not args:
                logger.info('Image scanner running...')
                queue = JobQueue(host=settings.BEANSTALKD_HOST,
                                 port=settings.BEANSTALKD_PORT,
                                 sub='tracking', logger=logger)
                while True:
                    job = None
                    try:
                        job = queue.get()
                        try:
                            job_details = json.loads(job.body)
                        except ValueError:
                            logger.error(
                                'Error in loading job body: %s' % job.body)
                            job.delete()
                            continue
                        logger.info(
                            'Scanning image post delivery for %s'
                            % job_details)
                        image_name = job_details['image_name']
                        image = ContainerImage.objects.get(name=image_name)
                        scan_image(image)
                    except Exception as e:
                        logger.error('Image scan error: %s' % e, exc_info=True)
                    finally:
                        if job:
                            job.delete()
        except Exception as e:
            logger.critical('imagescanner errored out: %s' % e,
                            exc_info=True)
            sys.exit(1)
