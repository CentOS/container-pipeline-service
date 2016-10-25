import time

from ci.tests.base import BaseTestCase
from ci.lib import _print


class TestOpenshift(BaseTestCase):
    node = 'openshift'

    def test_00_openshift_builds_are_complete(self):
        print "=" * 30
        print "Test if openshift builds are running"
        print "=" * 30
        cmd = (
            "oc login https://{openshift}:8443 "
            "--insecure-skip-tls-verify=true "
            "-u test-admin -p test > /dev/null && "
            "oc project bamachrn-python > /dev/null && "
            "oc get pods"
        ).format(openshift=self.hosts[self.node]['host'])
        self.run_cmd(cmd)
        retries = 0
        success = False
        while retries < 10 and success is False:
            if retries > 0:
                time.sleep(60)
            _print("Retries: %d/100" % retries)
            try:
                output = self.run_cmd(cmd)
                _print(output)
                lines = output.splitlines()
                pods = set([line.split()[0] for line in lines[1:]
                            if line and line.split()[2] == 'Completed'])
                success = not set(
                    # FIXME: we're ignoring delivery build right now as it will
                    # need the atomic scan host for that.
                    # ['build-1-build', 'delivery-1-build', 'test-1-build'])
                    ['build-1-build', 'test-1-build', 'delivery-1-build']
                ).difference(pods)
            except Exception:
                success = False
            retries += 1
        if success is False:
            raise Exception("Openshift builds did not complete.")
        _print("Openshift builds completed successfully.")

    def test_01_openshift_builds_persist_after_provision(self):
        self.provision(force=True)
        _print("=" * 30)
        _print("Test if openshift builds persist after reprovision")
        _print("=" * 30)
        cmd = (
            "oc login https://openshift:8443 --insecure-skip-tls-verify=true "
            "-u test-admin -p test > /dev/null && "
            "oc project bamachrn-python > /dev/null && "
            "oc get pods"
        )
        output = self.run_cmd(cmd)
        _print(output)
        lines = output.splitlines()
        pods = set([line.split()[0] for line in lines[1:]])
        success = set(
            # FIXME: we're ignoring delivery build right now as it will
            # need the atomic scan host for that.
            # ['build-1-build', 'delivery-1-build', 'test-1-build'])
            ['build-1-build', 'test-1-build', 'delivery-1-build']
        ).difference(pods)
        self.assertFalse(success)

    def test_02_pull_built_image(self):
        image = self.hosts['jenkins_slave']['host'] + \
            ':5000/bamachrn/python:release'
        cmd = (
            "sudo docker pull {image}"
        ).format(image=image)
        output = self.run_cmd(cmd)
        self.assertFalse('Error: ' in output)
