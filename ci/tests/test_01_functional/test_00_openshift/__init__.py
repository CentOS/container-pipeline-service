import time
import hashlib

from ci.tests.base import BaseTestCase
from ci.lib import _print


class TestOpenshift(BaseTestCase):
    node = 'openshift'

    def jenkinsProject(self, cmd, project, options=None):
        _print(self.run_cmd(
            str.format(
                "sudo java -jar /opt/jenkins-cli.jar -s http://localhost:8080 {cmd} {project}{options}",
                cmd=cmd,
                project=project,
                options="" if not options else options
            ),
            host=self.hosts['jenkins_master']['host']
        ))

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
        self.jenkinsProject("enable-job", "pipeline-ci-python-latest")
        self.jenkinsProject("build", "pipeline-ci-python-latest", " -f -v")
        self.jenkinsProject("disable-job", "pipeline-ci-python-latest")
        self.assertOsProjectBuildStatus(
            'c29e3d422555450d5ad0a2a178575e5640952a0046dd90fd33db80e4',
            ['build-1', 'test-1', 'delivery-1'],
            'Complete'
        )
        _print("Openshift builds completed successfully.")

    def test_01_pull_built_image(self):
        image = self.hosts['jenkins_slave']['host'] + \
            ':5000/pipeline-ci/python:latest'
        cmd = (
            "sudo docker pull {image}"
        ).format(image=image)
        output = self.run_cmd(cmd)
        self.assertFalse('Error: ' in output)

    def test_03_serialized_builds(self):
        self.cleanup_beanstalkd()
        self.cleanup_openshift()
        self.jenkinsProject("enable-job", "centos-kubernetes-master-latest")
        self.jenkinsProject("build", "centos-kubernetes-master-latest", " -f -v")
        self.jenkinsProject("disable-job", "centos-kubernetes-master-latest")

        time.sleep(5)

        # We are not testing jenkins' feature to trigger child builds,
        # so, we are triggering the child build manually, so that
        # we can avoid race condition between the builds
        self.jenkinsProject("enable-job", "centos-kubernetes-apiserver-latest")
        self.jenkinsProject("build", "centos-kubernetes-apiserver-latest", " -f -v")
        self.jenkinsProject("disable-job", "centos-kubernetes-apiserver-latest")


        k8s_master_os_project = hashlib.sha224(
            'centos-kubernetes-master-latest').hexdigest()
        k8s_apiserver_os_project = hashlib.sha224(
            'centos-kubernetes-apiserver-latest').hexdigest()

        # Wait for build worker to run build
        self.assertOsProjectBuildStatus(
            k8s_master_os_project, ['build-1'], 'Running', retries=40,
            delay=15)

        time.sleep(20)

        # Then assert that lock file for centos-kubernetes-master-latest exists
        self.assertTrue(self.run_cmd(
            'ls /srv/pipeline-logs/centos-kubernetes-master-latest'))
        self.assertOsProjectBuildStatus(
            k8s_master_os_project, ['build-1', 'test-1', 'delivery-1'],
            'Complete', retries=80, delay=15
        )

        # Assert that delivery of centos-kubernetes-master-latest triggered
        # build for centos-kubernetes-apiserver-latest
        self.assertOsProjectBuildStatus(
            k8s_apiserver_os_project, ['build-1'], 'Running', retries=40,
            delay=5)

        # Assert that lock file for centos-kubernetes-master-latest does not
        # exist anymore
        self.assertRaises(
            Exception,
            self.run_cmd,
            'ls /srv/pipeline-logs/centos-kubernetes-master-latest')
