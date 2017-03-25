from django.core.management.base import BaseCommand  # CommandError

from tracking.models import ContainerImage


class Command(BaseCommand):
    help = 'Trigger image builds due for building'

    def handle(self, *args, **options):
        to_build = set()
        qs = ContainerImage.objects.filter(to_build=True)
        for container in qs:
            if qs.filter(
                    id__in=[item.id for item in container.parents.all()]):
                try:
                    to_build.remove(container)
                except KeyError:
                    pass
            else:
                to_build.add(container)
        for c in to_build:
            c.trigger_build()
