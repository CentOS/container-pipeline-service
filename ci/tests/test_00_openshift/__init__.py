import time
import hashlib

from ci.tests.base import BaseTestCase
from ci.lib import _print


class TestOpenshift(BaseTestCase):
    node = 'openshift'

    def assertOsProjectBuildStatus(self, project, expected_builds,
                                   expected_state, retries=20, delay=60):
        print "=" * 30
        print "Test if openshift builds are running"
        print "=" * 30
        openshift_host = self.hosts['openshift']['host']
        oc_config = (
            '/var/lib/origin/openshift.local.config/master/admin.kubeconfig')
        cmd = (
            "oc --config {config} project {project} > /dev/null && "
            "oc --config {config} get builds".format(
                config=oc_config, project=project)
        )
        retry_count = 0
        success = False
        while retry_count < retries and success is False:
            if retry_count > 0:
                time.sleep(delay)
                _print("Retries: %d/%d" % (retry_count, retries))
            try:
                output = self.run_cmd(cmd, host=openshift_host)
                _print(output)
                lines = output.splitlines()
                pods = set([line.split()[0] for line in lines[1:]
                            if line and expected_state in line.split()])
                success = not set(
                    # FIXME: we're ignoring delivery build right now as it will
                    # need the atomic scan host for that.
                    # ['build-1', 'delivery-1', 'test-1'])
                    expected_builds
                ).difference(pods)
            except Exception:
                success = False
            retry_count += 1
        self.assertTrue(success)

    def test_00_openshift_builds_are_complete(self):
        self.provision()
        self.cleanup_openshift()
        self.cleanup_beanstalkd()
        print self.run_cmd(
            'java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 enable-job bamachrn-python-release',
            host=self.hosts['jenkins_master']['host'])
        print self.run_cmd(
            'java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 '
            'build bamachrn-python-release -f -v',
            host=self.hosts['jenkins_master']['host'])
        print self.run_cmd(
            'java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 disable-job bamachrn-python-release',
            host=self.hosts['jenkins_master']['host'])

        self.assertOsProjectBuildStatus(
            '53b1a8ddd3df5d4fd94756e8c20ae160e565a4b339bfb47165285955',
            ['build-1', 'test-1', 'delivery-1'],
            'Complete'
        )
        _print("Openshift builds completed successfully.")

    def test_01_pull_built_image(self):
        image = self.hosts['jenkins_slave']['host'] + \
            ':5000/bamachrn/python:release'
        cmd = (
            "sudo docker pull {image}"
        ).format(image=image)
        output = self.run_cmd(cmd)
        self.assertFalse('Error: ' in output)

    def test_03_serialized_builds(self):
        self.cleanup_beanstalkd()
        self.cleanup_openshift()
        _print(self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s '
            'http://localhost:8080 enable-job '
            'centos-kubernetes-master-latest',
            host=self.hosts['jenkins_master']['host']))
        _print(self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s '
            'http://localhost:8080 enable-job '
            'centos-kubernetes-apiserver-latest',
            host=self.hosts['jenkins_master']['host']))
        k8s_apiserver_prev_builds = self.get_jenkins_builds_for_job(
            'centos-kubernetes-apiserver-latest')
        _print(self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s http://localhost:8080 build '
            'centos-kubernetes-master-latest -f -v',
            host=self.hosts['jenkins_master']['host']
        ))
        time.sleep(10)
        k8s_apiserver_cur_builds = self.get_jenkins_builds_for_job(
            'centos-kubernetes-apiserver-latest')
        self.assertTrue(
            len(k8s_apiserver_cur_builds) > len(k8s_apiserver_prev_builds))
        _print(self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s '
            'http://localhost:8080 disable-job '
            'centos-kubernetes-master-latest',
            host=self.hosts['jenkins_master']['host']))
        _print(self.run_cmd(
            'java -jar /opt/jenkins-cli.jar -s '
            'http://localhost:8080 disable-job '
            'centos-kubernetes-apiserver-latest',
            host=self.hosts['jenkins_master']['host']))
        k8s_master_os_project = hashlib.sha224(
            'centos-kubernetes-master-latest').hexdigest()
        k8s_apiserver_os_project = hashlib.sha224(
            'centos-kubernetes-apiserver-latest').hexdigest()
        self.assertOsProjectBuildStatus(
            k8s_master_os_project, ['build-1', 'test-1', 'delivery-1'],
            'Complete'
        )

        # Assert that delivery of centos-kubernetes-master-latest triggered
        # build for centos-kubernetes-apiserver-latest
        self.assertOsProjectBuildStatus(
            k8s_apiserver_os_project, ['build-1'], 'Running', retries=6,
            delay=30)
        self.assertRaises(
            Exception,
            self.run_cmd,
            'ls /srv/pipeline-logs/centos-kubernetes-master-latest')
