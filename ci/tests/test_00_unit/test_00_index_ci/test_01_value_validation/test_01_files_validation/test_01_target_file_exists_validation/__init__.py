from ci.tests.test_00_unit.test_00_index_ci.test_01_value_validation. \
    test_01_files_validation.file_validation_base import FilesBaseTest
from ci.tests.test_00_unit.test_00_index_ci.indexcibase import DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.value_validation as value_validation


class TargetFileExistsValidationTests(FilesBaseTest):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_success_target_file_exists(self):
        s, mock_loc = self.setup_mock_location(
            {
                "Dockerfile": None
            }
        )
        self.assertTrue(
            value_validation.TargetFileExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.TARGET_FILE: "Dockerfile",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_fails_target_file_missing(self):
        s, mock_loc = self.setup_mock_location(
            {}
        )
        self.assertFalse(
            value_validation.TargetFileExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.TARGET_FILE: "Dockerfile",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
