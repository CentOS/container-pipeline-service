from ci.tests.base import BaseTestCase
from ci.vendors import beanstalkc
import sys
import os
import json
import time
from xml.dom.minidom import parseString
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
            'cd /opt/cccp-service/src && '
            './manage.py flush --noinput')

    def run_dj_script(self, script):
        _script = (
            'import os, django; '
            'os.environ.setdefault(\\"DJANGO_SETTINGS_MODULE\\", '
            '\\"container_pipeline.settings\\"); '
            '{}'
        ).format(script)
        return self.run_cmd(
            'cd /opt/cccp-service/src && '
            'python -c "{}"'.format(_script))

    def get_jenkins_builds_for_job(self, job):
        s = self.run_cmd('curl -g "http://localhost:8080/job/%s/api/xml?'
                         'tree=allBuilds[result,number]&"' % job).strip()
        dom = parseString(s)
        builds = [child.getElementsByTagName('number')[0].childNodes[0].data
                  for child in dom.childNodes[0].childNodes]
        return builds

    def test_00_if_fetch_scan_image_job_is_successful(self):
        self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 '
            'enable-job fetch-scan-image')
        print self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 '
            'build fetch-scan-image -f -v')
        self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 '
            'disable-job fetch-scan-image')
        out = self.run_dj_script(
                    'from tracking.models import ContainerImage; '
                    'print ContainerImage.objects.all().count()')
        print 'Images fetched', out.strip()
        self.assertTrue(int(out.strip()))
        out = self.run_dj_script('from tracking.models import Package; '
                                 'print Package.objects.all().count()')
        print 'Packages found', out.strip()
        self.assertTrue(int(out.strip()) > 0)

    def test_01_image_delivery_triggers_image_scan(self):
        # Create ContainerImage for bamachrn/python:release
        # In the real world, it will be created automatically by
        # fetch-scan-image job which gets run after cccp-index job
        self.run_dj_script(
            'from tracking.models import ContainerImage; '
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
                    'from tracking.models import ContainerImage; '
                    'print ContainerImage.objects.get('
                    'name=\\"bamachrn/python:release\\").scanned').strip()
            if scanned == 'True':
                is_scanned = True
                break
            time.sleep(10)
        self.assertTrue(is_scanned)

        time.sleep(10)

        # Assert that image package data was populated
        self.assertTrue(
            int(
                self.run_dj_script(
                    'from tracking.models import ContainerImage; '
                    'print ContainerImage.objects.get('
                    'name=\\"bamachrn/python:release\\").packages.count()'
                ).strip()
            ) > 0
        )

    def test_02_pkg_change_handler(self):
        repoinfo_id = self.run_dj_script(
            'from tracking.models import ContainerImage, Package, RepoInfo; '
            'repo = RepoInfo.objects.create('
            'baseurls=\\"foo\\", basearch=\\"x86_64\\", releasever=\\"7\\", '
            'infra=\\"container\\"); '
            'image = ContainerImage.objects.create('
            'name=\\"bamachrn/python:release\\", repoinfo=repo); '
            'pkg = Package.objects.create(name=\\"abc\\", arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'image.packages.add(pkg); image.save(); print repo.id'
        ).strip()

        # Different package, same upstream does not mark image for build
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange foo-2.8.5-48.el7.x86_64 %s'
            % repoinfo_id)
        time.sleep(2)
        self.assertEqual(
            self.run_dj_script('from tracking.models import ContainerImage; '
                               'print ContainerImage.objects.get('
                               'name=\\"bamachrn/python:release\\")'
                               '.to_build').strip(),
            'False')
        # Same package, same upstream does not mark image for build
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange foo-1.2-1.el7.x86_64 %s'
            % repoinfo_id)
        time.sleep(2)
        self.assertEqual(
            self.run_dj_script('from tracking.models import ContainerImage; '
                               'print ContainerImage.objects.get('
                               'name=\\"bamachrn/python:release\\")'
                               '.to_build').strip(),
            'False')
        # Package change, different upstream does not mark image for build
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange abc-1.3-1.el7.x86_64 %s'
            % repoinfo_id + '1')
        time.sleep(2)
        self.assertEqual(
            self.run_dj_script('from tracking.models import ContainerImage; '
                               'print ContainerImage.objects.get('
                               'name=\\"bamachrn/python:release\\")'
                               '.to_build').strip(),
            'False')
        # Package change, same upstream marks image for build
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange abc-1.3-1.el7.x86_64 %s'
            % repoinfo_id)
        time.sleep(2)
        self.assertEqual(
            self.run_dj_script('from tracking.models import ContainerImage; '
                               'print ContainerImage.objects.get('
                               'name=\\"bamachrn/python:release\\")'
                               '.to_build').strip(),
            'True')
        self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 '
            'enable-job bamachrn-python-release')
        prev_builds = self.get_jenkins_builds_for_job(
            'bamachrn-python-release')
        time.sleep(20)
        cur_builds = self.get_jenkins_builds_for_job(
            'bamachrn-python-release')
        self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 '
            'disable-job bamachrn-python-release')
        self.assertTrue(len(cur_builds) > len(prev_builds))
        self.cleanup_openshift()

    def test_03_package_change_effect_on_dependent_images(self):
        """
        This tests handling package change for a set of dependent
        container images:
                                image1 {pkg1}
                                /    \
             {pkg1, pkg2} image2      image3 {pkg1, pkg3}
                         /
                         image4 {pkg1, pkg2, pkg4}
                               \
                               image5 {pkg1, pkg2, pkg4, pkg5}
        """
        repoinfo_id = self.run_dj_script(
            'from tracking.models import ContainerImage, Package, RepoInfo; '
            'repo = RepoInfo.objects.create('
            'baseurls=\\"foo\\", basearch=\\"x86_64\\", releasever=\\"7\\", '
            'infra=\\"container\\"); '
            'image1 = ContainerImage.objects.create('
            'name=\\"image1\\", repoinfo=repo); '
            'image2 = ContainerImage.objects.create('
            'name=\\"image2\\", repoinfo=repo); '
            'image3 = ContainerImage.objects.create('
            'name=\\"image3\\", repoinfo=repo); '
            'image4 = ContainerImage.objects.create('
            'name=\\"image4\\", repoinfo=repo); '
            'image5 = ContainerImage.objects.create('
            'name=\\"image5\\", repoinfo=repo); '
            'image5.parents.add(image1, image2, image4); '
            'image5.save(); '
            'image4.parents.add(image1, image2); image4.save(); '
            'image3.parents.add(image1); image3.save(); '
            'image2.parents.add(image1); image2.save(); '
            'pkg1 = Package.objects.create(name=\\"pkg1\\", '
            'arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'pkg1.images.add(image1, image2, image3, image4, image5); '
            'pkg1.save(); '
            'pkg2 = Package.objects.create(name=\\"pkg2\\", '
            'arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'pkg2.images.add(image2, image3, image4, image5); '
            'pkg2.save(); '
            'pkg3 = Package.objects.create(name=\\"pkg3\\", '
            'arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'pkg3.images.add(image3); '
            'pkg3.save(); '
            'pkg4 = Package.objects.create(name=\\"pkg4\\", '
            'arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'pkg4.images.add(image4, image5); '
            'pkg4.save(); '
            'pkg5 = Package.objects.create(name=\\"pkg5\\", '
            'arch=\\"x86_64\\", '
            'version=\\"1.2\\", release=\\"1.el7\\"); '
            'pkg5.images.add(image5); '
            'pkg5.save(); '
        ).strip()
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange pkg2-1.3-1.el7.x86_64 %s'
            % repoinfo_id)
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange pkg3-1.3-1.el7.x86_64 %s'
            % repoinfo_id)
        self.run_cmd(
            'cd /opt/cccp-service/src && '
            './manage.py emitpkgchange pkg5-1.3-1.el7.x86_64 %s'
            % repoinfo_id)
        time.sleep(2)
        self.assertEqual(
            self.run_dj_script(
                'from tracking.models import ContainerImage; '
                'print ContainerImage.objects.filter(to_build=True)'
                '.order_by(\\"name\\")').strip(),
            '[<ContainerImage: image2>, <ContainerImage: image3>, '
            '<ContainerImage: image4>, <ContainerImage: image5>]')
        time.sleep(20)
        self.assertEqual(
            self.run_dj_script(
                'from tracking.models import ContainerImage; '
                'print ContainerImage.objects.filter(to_build=True)'
                '.order_by(\\"name\\")').strip(),
            '[<ContainerImage: image2>, <ContainerImage: image3>]')

    def test_04_process_upstream_repo(self):
        # cleanup
        try:
            os.remove('/tmp/repodata_1.json')
        except:
            pass

        # setup
        sys.path.append(os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../src'))
        )
        from tracking.lib.repo import process_upstream
        added, modified, removed = process_upstream('1', {
            'baseurls': ['http://mirrors.uprm.edu/centos/7/os/x86_64/'],
            'basearch': 'x86_64'}, '/tmp')

        added, modified, removed = process_upstream('1', {
            'baseurls': [
                'http://mirrors.uprm.edu/centos/7/os/x86_64/',
                'http://mirrors.uprm.edu/centos/7/updates/x86_64/'
            ],
            'basearch': 'x86_64'}, '/tmp')

        # Check if item[0] is None and item[1] is not None for item in added
        for item in added:
            self.assertFalse(item[0])
            self.assertTrue(item[1])

        # Check if name, arch of item[0] and item[0] are same for item in
        # modified
        for item in modified:
            self.assertEqual(
                (item[0][0], item[0][1]), (item[1][0], item[1][1]))
            # Assert that none of the new package has version less than the
            # old package
            self.assertFalse(
                LooseVersion(item[1][-2]) < LooseVersion(item[0][-2]))
            # Assert that none of the new package whose version is equal to
            # the old package has a release less than that of the old package
            self.assertFalse(
                LooseVersion(item[1][-2]) == LooseVersion(item[0][-2]) and
                LooseVersion(item[1][-1]) < LooseVersion(item[0][-1]))

        # Check if item[0] is not None and item[1] is None for item in removed
        for item in removed:
            self.assertFalse(item[1])
            self.assertTrue(item[0])
