from ci.tests.test_00_unit.test_05_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class GitUrlValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_job_id(self):
        self.assertTrue(
            schema_validation.GitURLValidator(
                {
                    FieldKeys.GIT_URL: "https://github.com/test/test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_git_url(self):
        self.assertFalse(
            schema_validation.GitURLValidator(
                {
                    "Git-URL": "https://github.com/test/test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_git_url_not_string(self):
        self.assertFalse(
            schema_validation.JobIDValidator(
                {
                    FieldKeys.GIT_URL: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
