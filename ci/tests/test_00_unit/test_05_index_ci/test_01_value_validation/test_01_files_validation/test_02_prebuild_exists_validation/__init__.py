from ci.tests.test_00_unit.test_05_index_ci.test_01_value_validation. \
    test_01_files_validation.file_validation_base import FilesBaseTest
from ci.tests.test_00_unit.test_05_index_ci.indexcibase import DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.value_validation as value_validation


class PrebuildValidationTests(FilesBaseTest):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_success_no_prebuild_script(self):
        s, mock_loc = self.setup_mock_location(
            {}
        )
        self.assertTrue(
            value_validation.PreBuildExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_success_valid_prebuild_script_prebuild_context(self):
        s, mock_loc = self.setup_mock_location(
            {
                "test.sh": "testing 1 2 3",
                "pre_context": None
            }
        )
        self.assertTrue(
            value_validation.PreBuildExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.PREBUILD_SCRIPT: "/test.sh",
                    FieldKeys.PREBUILD_CONTEXT: "/pre_context",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_fails_prebuild_script_does_not_exist(self):
        s, mock_loc = self.setup_mock_location(
            {
                "test.sh": "testing 1 2 3",
                "pre_context": None
            }
        )
        self.assertFalse(
            value_validation.PreBuildExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.PREBUILD_SCRIPT: "/does_not_exist.sh",
                    FieldKeys.PREBUILD_CONTEXT: "/pre_context",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_04_fails_prebuild_script_exists_no_prebuild_context(self):
        s, mock_loc = self.setup_mock_location(
            {
                "test.sh": "testing 1 2 3",
                "pre_context": None
            }
        )
        self.assertFalse(
            value_validation.PreBuildExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.PREBUILD_SCRIPT: "/test.sh",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_05_fails_prebuild_script_exists_invalid_prebuild_context(self):
        s, mock_loc = self.setup_mock_location(
            {
                "test.sh": "testing 1 2 3",
                "pre_context": None
            }
        )
        self.assertFalse(
            value_validation.PreBuildExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    FieldKeys.PREBUILD_SCRIPT: "/test.sh",
                    FieldKeys.PREBUILD_CONTEXT: "/pre_context1",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
