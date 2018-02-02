# module to test scanner functionality

import os
import time

from random import randint
from ci.tests.base import BaseTestCase
from container_pipeline.lib.settings import SCANNERS_RESULTFILE,\
        SCANNERS_STATUS_FILE

BUILD_FAIL_PROJECT_NAME = "nshaikh-go-helloworld-latest"


class TestScanners(BaseTestCase):
    """
    Module to test linter functionalities.
    """
    node = 'scanner'

    def setUp(self):
        """
        Set Up needed environment for testing.
        Initialize the beanstalkd queue with queues respective to linter.
        """
        super(TestScanners, self).setUp()
        # project name generated from appid-jobid-tag
        self.project_under_test = BUILD_FAIL_PROJECT_NAME
        # initialize projects model, to simulate cccp-index job
        self.appid = "nshaikh"
        self.jobid = "go-helloworld"
        self.desired_tag = "latest"
        self.repo_url = "https://github.com/navidshaikh/minimal-go-container"
        self.repo_branch = "master"
        self.repo_build_path = "/"
        self.target_file = "Dockerfile.scratch"
        self.depends_on = "centos/centos:latest"
        self.test_tag = "SCANNERS_TEST"
        self.logs_dir = "/srv/pipeline-logs/" + self.test_tag
        self.build_context = "./"
        self.build_number = str(randint(11, 99))
        self.notify_email = "container-status-report@centos.org"
        self.cleanup_beanstalkd()
        self.cleanup_openshift()

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

    def start_build(self):
        """
        Starts the build of a project
        """
        self.provision()
        # create database entry for Project model for project under test
        self.run_dj_script(
            'from container_pipeline.models import Project; '
            'Project.objects.get_or_create('
            'name=\\"nshaikh-go-helloworld-latest\\")'
        )
        workspace_dir = os.path.join(
            "/srv/jenkins/workspace/",
            self.project_under_test)

        # run the container_pipeline/pipeline.py module
        args = " ".join([
            self.appid, self.jobid, self.repo_url,
            self.repo_branch, self.repo_build_path,
            self.target_file, self.notify_email,
            self.desired_tag, self.depends_on,
            self.test_tag, self.build_number,
            self.build_context])

        command = ("mkdir -p {0} && "
                   "git clone {1} {0} && "
                   "export DOCKERFILE_DIR={0} && "
                   "export PYTHONPATH=/opt/cccp-service && "
                   "mkdir -p /srv/pipeline-logs/{2} && "
                   "cd /opt/cccp-service && "
                   "python container_pipeline/pipeline.py {3}").format(
            workspace_dir, self.repo_url, self.test_tag, args)

        # we need to trigger build on jenkins_slave node
        # figure out jenkins_slave hostname to run command upon
        # self.hosts variable is defined in base.py
        jenkins_slave = self.hosts["jenkins_slave"]["host"]

        print "Starting a test build with command: \n%s" % command
        print self.run_cmd(command, host=jenkins_slave)

    def check_if_file_exists(self, path):
        """
        Checks if given filepath exists
        """
        retry_count = 0
        is_present = False
        while retry_count < 10:
            retry_count += 1
            print "Check if file %s exists: " % path
            if self.run_cmd(
                    "[ ! -f {0} ] || echo 'Yes';".format(
                        path)).strip() == "Yes":
                is_present = True
                break
            print "File not found, waiting and retrying.. "
            time.sleep(60)
        print self.run_cmd("ls {0}".format(os.path.dirname(path)))
        return is_present

    def test_00_rpm_verify_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # start the build, at the start of very first test
        self.start_build()
        # wait for 120 seconds to complete the build
        time.sleep(120)
        # get the relevant result file for scanner to be tested
        result_file = SCANNERS_RESULTFILE.get(
                "registry.centos.org/pipeline-images/scanner-rpm-verify"
                )[0]
        self.assertTrue(self.check_if_file_exists(
            path=os.path.join(self.logs_dir, result_file)
        ))

    def test_01_misc_package_updates_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # get the relevant result file for scanner to be tested
        result_file = SCANNERS_RESULTFILE.get(
                "registry.centos.org/pipeline-images/misc-package-updates"
                )[0]
        self.assertTrue(self.check_if_file_exists(
            path=os.path.join(self.logs_dir, result_file)
        ))

    def test_02_pipeline_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # get the relevant result file for scanner to be tested
        result_file = SCANNERS_RESULTFILE.get(
                "registry.centos.org/pipeline-images/pipeline-scanner"
                )[0]
        # since pipeline scanner will fail to execute for containers with
        # minimal golang executables and images without yum installed
        self.assertFalse(self.check_if_file_exists(
            path=os.path.join(self.logs_dir, result_file)
        ))

    def test_03_container_capabilities_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # get the relevant result file for scanner to be tested
        result_file = SCANNERS_RESULTFILE.get(
                "registry.centos.org/pipeline-images/"
                "container-capabilities-scanner"
                )[0]
        self.assertTrue(self.check_if_file_exists(
            path=os.path.join(self.logs_dir, result_file)
        ))

    def test_04_scanner_execution_status(self):
        """
        Test if scanner is exporting the execution status file.
        """
        self.assertTrue(self.check_if_file_exists(
            path=os.path.join(self.logs_dir, SCANNERS_STATUS_FILE)
        ))

    def tearDown(self):
        """
        Tear down tests artifacts
        """
        self.cleanup_beanstalkd()
        self.cleanup_openshift()
