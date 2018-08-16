from ci.tests.test_00_unit.test_00_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class JobIDValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_job_id(self):
        self.assertTrue(
            schema_validation.JobIDValidator(
                {
                    FieldKeys.JOB_ID: "test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_job_id(self):
        self.assertFalse(
            schema_validation.JobIDValidator(
                {
                    "Job-Id": "test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_job_id_not_string(self):
        self.assertFalse(
            schema_validation.JobIDValidator(
                {
                    FieldKeys.JOB_ID: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
