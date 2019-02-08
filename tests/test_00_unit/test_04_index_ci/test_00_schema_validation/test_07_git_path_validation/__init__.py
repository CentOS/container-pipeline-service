from tests.test_00_unit.test_04_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class GitPathValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_job_id(self):
        self.assertTrue(
            schema_validation.GitPathValidator(
                {
                    FieldKeys.GIT_PATH: "/"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_git_path(self):
        self.assertFalse(
            schema_validation.GitPathValidator(
                {
                    "Git-Path": "/"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_git_path_not_string(self):
        self.assertFalse(
            schema_validation.GitPathValidator(
                {
                    FieldKeys.GIT_PATH: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
