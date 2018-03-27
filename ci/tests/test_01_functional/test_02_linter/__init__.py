# module to test linter functionality

import os
import time

from random import randint
from ci.tests.base import BaseTestCase
from ci.constants import LINTER_RESULT_FILE,\
    LINTER_STATUS_FILE

BUILD_FAIL_PROJECT_NAME = "nshaikh-build-fail-test-latest"


class TestLinter(BaseTestCase):
    """
    Module to test linter functionalities.
    """
    node = 'jenkins_slave'

    def setUp(self):
        """
        Set Up needed environment for testing.
        Initialize the beanstalkd queue with queues respective to linter.
        """
        super(TestLinter, self).setUp()
        # project name generated from appid-jobid-tag
        self.project_under_test = BUILD_FAIL_PROJECT_NAME
        # initialize projects model, to simulate cccp-index job
        self.appid = "nshaikh"
        self.jobid = "build-fail-test"
        self.desired_tag = "latest"
        self.repo_url = "https://github.com/navidshaikh/fail-test-container"
        self.repo_branch = "master"
        self.repo_build_path = "/"
        self.target_file = "Dockerfile"
        self.depends_on = "centos/centos:latest"
        self.test_tag = "LINTER_TEST"
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
            'from container_pipeline.utils import form_targetfile_link;'
            'p, c = Project.objects.get_or_create('
            'name=\\"nshaikh-build-fail-test-latest\\");'
            'p.target_file_link=form_targetfile_link('
            '{}, {}, {}, {}'
            ');'
            'p.save()'.format(
                self.repo_url,
                self.repo_build_path,
                self.repo_branch,
                self.target_file
            )
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
        print "Starting a test build with command: \n%s" % command
        print self.run_cmd(command)

    def check_if_linter_exported_results(self, path):
        """
        Checks if linter results exists
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
        return is_present

    def test_00_linter_results(self):
        """
        Test if linter is exporting the results as expected.
        """
        self.start_build()
        self.assertTrue(self.check_if_linter_exported_results(
            path=os.path.join(self.logs_dir, LINTER_RESULT_FILE)
        ))

    def test_01_linter_execution_status(self):
        """
        Test if linter execution status file is exported
        """
        self.assertTrue(self.check_if_linter_exported_results(
            path=os.path.join(self.logs_dir, LINTER_STATUS_FILE)
        ))

    def tearDown(self):
        """
        Tear down tests artifacts
        """
        self.cleanup_beanstalkd()
        self.cleanup_openshift()
