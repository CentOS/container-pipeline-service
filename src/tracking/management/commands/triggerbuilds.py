import time

from django.core.management.base import BaseCommand  # CommandError
from django.utils import timezone
from django.conf import settings

from tracking.models import ContainerImage, Package


class Command(BaseCommand):
    help = 'Trigger image builds due for building'

    def handle(self, *args, **options):
        while True:
            last_updated = Package.objects.all().order_by(
                '-last_updated')[0].last_updated
            if (timezone.now() - last_updated).seconds < (
                    settings.CONTAINER_BUILD_TRIGGER_DELAY):
                time.sleep(10)
                continue
            to_build = set()
            qs = ContainerImage.objects.filter(to_build=True)
            for container in qs:
                if qs.filter(
                        id__in=[item.id for item in container.parents.all()]):
                    try:
                        to_build.remove(container)
                        container.to_build = False
                        container.save()
                    except KeyError:
                        pass
                else:
                    to_build.add(container)
            for c in to_build:
                c.trigger_build()
                c.to_build = False
                c.save()
