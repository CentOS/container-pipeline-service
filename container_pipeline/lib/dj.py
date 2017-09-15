import django
import os


def load():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'container_pipeline.lib.settings')
    django.setup()
