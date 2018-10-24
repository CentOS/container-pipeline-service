import os
import unittest

from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.lib.constants.jenkins import JENKINS_CLASS, JENKINS_SHORT_DESCRIPTION


class TestBuildInfo(unittest.TestCase):

    def setUp(self):
        self.build_info = OpenshiftJenkinsBuildInfo(
            jenkins_server="test",
            test=True,
            namespace="cccp"
        )
        self.ordered_job_list = [
            "cccp", "bamachrn-python-release"
        ]
        self.build_number = "1"

    def test_00_gets_correct_build_count(self):
        self.setUp()
        test_data = [
            {
                "build": 1
            },
            {
                "build": 2
            }
        ]
        expected = "2"
        actual = self.build_info.get_builds_count(
            ordered_job_list=self.ordered_job_list,
            test_data_set=test_data
        )
        self.assertEqual(expected, str(actual))

    def test_01_gets_correct_build_status(self):
        self.setUp()
        test_data = {
            "result": "SUCCESS"
        }
        expected = "SUCCESS"
        actual = self.build_info.get_build_status(
            ordered_job_list=self.ordered_job_list,
            build_number=self.build_number,
            test_data_set=test_data
        )
        self.assertEqual(expected, str(actual))

    def test_02_gets_correct_cause_of_first_build(self):
        self.setUp()
        test_data = {
            "number": 1
        }
        expected = "First build of the container image"
        actual = self.build_info.get_cause_of_build(
            ordered_job_list=self.ordered_job_list,
            build_number=self.build_number,
            test_data_set=test_data
        )["cause"]
        self.assertEqual(expected, str(actual))

    def test_03_gets_correct_cause_of_build_scm_trigger(self):
        self.setUp()
        test_data = {
            "number": 2,
            "actions": [
                {
                    JENKINS_CLASS: "hudson.model.CauseAction",
                    "causes": [
                        {
                            JENKINS_CLASS:
                                "hudson.triggers.SCMTrigger$SCMTriggerCause",
                            JENKINS_SHORT_DESCRIPTION:
                                "Triggered by git commit blah"
                        }
                    ]
                }
            ]
        }
        expected = "Triggered by git commit blah"
        actual = self.build_info.get_cause_of_build(
            ordered_job_list=self.ordered_job_list,
            build_number=self.build_number,
            test_data_set=test_data
        )["cause"]
        self.assertEqual(expected, str(actual))
