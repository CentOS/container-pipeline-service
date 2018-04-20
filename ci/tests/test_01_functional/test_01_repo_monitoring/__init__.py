from ci.tests.base import BaseTestCase
from ci.vendors import beanstalkc
import sys
import os
import json
import time
from distutils.version import LooseVersion


class TestRepoMonitoring(BaseTestCase):
    node = 'jenkins_master'

    def setUp(self):
        super(TestRepoMonitoring, self).setUp()
        self.cleanup_openshift()
        self.cleanup_beanstalkd()
        self._teardown()

    def tearDown(self):
        self._teardown()

    def _teardown(self):
        self.run_cmd(
            'cd /opt/cccp-service && '
            './manage.py flush --noinput')

    def run_dj_script(self, script):
        _script = (
            'import os, django; '
            'os.environ.setdefault(\\"DJANGO_SETTINGS_MODULE\\", '
            '\\"container_pipeline.lib.settings\\"); '
            'django.setup(); '
            '{}'
        ).format(script)
        return self.run_cmd(
            'cd /opt/cccp-service && '
            'python -c "{}"'.format(_script))

    def test_01_image_delivery_triggers_image_scan(self):
        # Create ContainerImage for bamachrn/python:release
        # In the real world, it will be created automatically by
        # fetch-scan-image job which gets run after cccp-index job
        self.run_dj_script(
            'from container_pipeline.models.pipeline import ContainerImage; '
            'ContainerImage.objects.create('
            'name=\\"bamachrn/python:release\\")')

        # simulate image delivery
        bs = beanstalkc.Connection(self.hosts['openshift']['host'])
        bs.use('tracking')
        bs.put(json.dumps({'image_name': 'bamachrn/python:release'}))

        time.sleep(10)
        retries = 0

        is_scanned = False
        while retries < 50:
            retries += 1
            # Assert that image got scanned
            scanned = self.run_dj_script(
                'from container_pipeline.models.pipeline import '
                'ContainerImage; '
                'print ContainerImage.objects.get('
                'name=\\"bamachrn/python:release\\").scanned').strip()
            print "Is scanned: {}".format(scanned)
            if scanned:
                print "Is scanned: {}".format(scanned)
            if scanned == 'True':
                is_scanned = True
                break
            time.sleep(5)

        print self.run_cmd("docker images")
        self.assertTrue(is_scanned)

        time.sleep(10)

        # Assert that image package data was populated
        self.assertTrue(
            int(
                self.run_dj_script(
                    'from container_pipeline.models.pipeline import '
                    'ContainerImage; '
                    'print ContainerImage.objects.get('
                    'name=\\"bamachrn/python:release\\").packages.count()'
                ).strip()
            ) > 0
        )
