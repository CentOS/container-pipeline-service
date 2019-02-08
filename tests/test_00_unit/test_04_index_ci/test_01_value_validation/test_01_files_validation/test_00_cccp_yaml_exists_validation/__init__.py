from tests.test_00_unit.test_04_index_ci.test_01_value_validation.\
    test_01_files_validation.file_validation_base import FilesBaseTest
from tests.test_00_unit.test_04_index_ci.indexcibase import DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.value_validation as value_validation


class CccpYamlExistsValidationTests(FilesBaseTest):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_succeeds_cccp_yaml_exists(self):
        s, mock_loc = self.setup_mock_location(
            {
                "cccp.yaml": "id: test"
            }
        )
        self.assertTrue(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_succeeds_dot_cccp_yaml_exists(self):
        s, mock_loc = self.setup_mock_location(
            {
                ".cccp.yaml": "id: test"
            }
        )
        self.assertTrue(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_succeeds_cccp_yml_exists(self):
        s, mock_loc = self.setup_mock_location(
            {
                "cccp.yml": "id: test"
            }
        )
        self.assertTrue(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_04_succeeds_dot_cccp_yml_exists(self):
        s, mock_loc = self.setup_mock_location(
            {
                ".cccp.yml": "id: test"
            }
        )
        self.assertTrue(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_05_fails_no_cccp_yaml_exists(self):
        s, mock_loc = self.setup_mock_location(
            {}
        )
        self.assertFalse(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_06_succeeds_no_cccp_yaml_but_prebuild_specified(self):
        s, mock_loc = self.setup_mock_location(
            {}
        )
        self.assertTrue(
            value_validation.CCCPYamlExistsValidator(
                {
                    CheckKeys.CLONE: False,
                    CheckKeys.CLONE_LOCATION: mock_loc,
                    FieldKeys.GIT_PATH: "/",
                    CheckKeys.STATE: s
                },
                DUMMY_INDEX_FILE
            )
        )
