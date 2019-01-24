from ci.tests.test_00_unit.test_00_index_ci.test_01_value_validation. \
    test_01_files_validation.file_validation_base import FilesBaseTest
from ci.tests.test_00_unit.test_00_index_ci.indexcibase import DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.value_validation as value_validation


class JobIDMatchesValidationTests(FilesBaseTest):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_success_job_id_cccp_yaml_matches_index(self):
        s, mock_loc = self.setup_mock_location(
            {
                "cccp.yaml": "{}: test".format(FieldKeys.JOB_ID)
            }
        )
        self.assertTrue(
            value_validation.JobIDMatchesIndex(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.JOB_ID: "test",
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_fails_no_job_id_in_cccp_yaml(self):
        s, mock_loc = self.setup_mock_location(
            {
                "cccp.yaml": "Job-Id: testx"
            }
        )
        self.assertFalse(
            value_validation.JobIDMatchesIndex(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.JOB_ID: "test",
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_fails_job_id_cccp_yaml_mismatch_index(self):
        s, mock_loc = self.setup_mock_location(
            {
                "cccp.yaml": "{}: testx".format(FieldKeys.JOB_ID)
            }
        )
        self.assertFalse(
            value_validation.JobIDMatchesIndex(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.JOB_ID: "test",
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
