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
            "sudo oc --config {config} project {project} > /dev/null && "
            "sudo oc --config {config} get builds".format(
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
            'sudo java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 enable-job bamachrn-python-release',
            host=self.hosts['jenkins_master']['host'])
        print self.run_cmd(
            'sudo java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 '
            'build bamachrn-python-release -f -v',
            host=self.hosts['jenkins_master']['host'])
        print self.run_cmd(
            'sudo java -jar /opt/jenkins-cli.jar '
            '-s http://localhost:8080 disable-job bamachrn-python-release',
            host=self.hosts['jenkins_master']['host'])
