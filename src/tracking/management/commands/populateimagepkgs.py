from django.core.management.base import BaseCommand  # CommandError

from tracking.models import ContainerImage, Package


class Command(BaseCommand):
    help = 'Populate RPM packages data for container images'
    args = '[<image_name1> <image_name2> ...]'

    def handle(self, *args, **options):
        filters = {}
        if args:
            filters['name__in'] = args
        for container in ContainerImage.objects.filter(**filters):
            container.pull()
            output = container.run('rpm -qa')
            packages = []
            for line in output.splitlines():
                if not line:
                    continue
                a, b = line.rsplit('-', 1)
                name, version = a.rsplit('-', 1)
                try:
                    release, arch = b.rsplit('.', 1)
                except ValueError:
                    release, arch = b, ''
                p, created = Package.objects.get_or_create(
                    name=name, version=version, release=release, arch=arch)
                packages.append(p)
            container.packages.add(*packages)
