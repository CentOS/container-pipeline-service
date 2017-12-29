# module to test linter functionality

import json
import os
import time
import uuid

from random import randint
from ci.tests.base import BaseTestCase
from container_pipeline.models import Project
from container_pipeline.utils import get_job_hash
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
        super(BaseTestCase, self).setUp(
            sub="master_tube",
            pub="master_tube")
        # project name generated from appid-jobid-tag
        self.project_under_test = BUILD_FAIL_PROJECT_NAME
        # initialize projects model, to simulate cccp-index job
        Project.objects.get_or_create(name=self.project_under_test)
        self.appid = "nshaikh"
        self.jobid = "build-fail-test"
        self.desired_tag = "latest"
        self.repo_url = "https://github.com/navidshaikh/containers-catalogue"
        self.repo_branch = "master"
        self.repo_build_path = "fail-test"
        self.target_file = "Dockerfile"
        self.depends_on = "centos/centos:latest"
        self.test_tag = "latest"
        self.build_context = "./"
        self.cleanup_beanstalkd()
        self.cleanup_openshift()

    def job_data(self):
        """
        Populate job data needed to put on tube
        """
        self.test_tag = self.run_cmd(
            "date +%s%N | md5sum | base64 | head -c 14")
        job = {}
        job["uuid"] = str(uuid.uuid4())
        job["appid"] = "nshaikh"
        job["jobid"] = "build-fail-test"
        job["notify_email"] = "container-status-report@centos.org"
        job["logs_dir"] = "/srv/pipeline-logs/{}".format(self.test_tag)
        job["action"] = "start_linter"
        job["job_id"] = self.jobid
        job["repo_url"] = self.repo_url
        job["repo_branch"] = self.repo_branch
        job["repo_build_path"] = self.repo_build_path
        job["target_file"] = self.target_file
        job["desired-tag"] = self.desired_tag
        job["depends_on"] = self.depends_on
        job["jenkins_build_number"] = randint(11, 99)
        job["project_name"] = self.project_under_test
        job["namespace"] = self.project_under_test
        job["project_hash_key"] = get_job_hash(self.project_under_test)
        job["job_name"] = self.project_under_test
        job["image_name"] = "{}/{}:{}".format(
            self.appid, self.jobid, self.desired_tag)
        job["output_image"] = "registry.centos.org/{}".format(
            job["image_name"])
        job["beanstalk_server"] = self.hosts["openshift"]["host"]
        job["image_under_test"] = job["output_image"]
        job["build_context"] = self.build_context
        return job

    def start_build(self):
        """
        Starts the build of a project
        """
        self.provision()
        self.queue.put(json.dumps(self.job_data()))

    def check_if_linter_exported_results(self, path):
        """
        Checks if linter results exists
        """
        retry_count = 0
        is_present = False
        while retry_count < 10:
            retry_count += 1
            if os.path.isfile(path):
                is_present = True
                break
            time.sleep(60)
        return is_present

    def test_00_linter_results(self):
        """
        Test if linter is exporting the results as expected.
        """
        self.start_build()
        self.assertTrue(self.check_if_linter_exported_results(
            path=os.path.join(self.job["logs_dir"], LINTER_RESULT_FILE)
        ))

    def test_01_linter_execution_status(self):
        """
        Test if linter execution status file is exported
        """
        self.assertTrue(self.check_if_linter_exported_results(
            path=os.path.join(self.job["logs_dir"], LINTER_STATUS_FILE)
        ))

    def tearDown(self):
        """
        Tear down tests artifacts
        """
        self.cleanup_beanstalkd()
        self.cleanup_openshift()
