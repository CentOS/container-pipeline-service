from ci.tests.test_00_unit.test_05_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class TargetFileValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_target_file(self):
        self.assertTrue(
            schema_validation.TargetFileValidator(
                {
                    FieldKeys.TARGET_FILE: "Dockerfile"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_target_file(self):
        self.assertFalse(
            schema_validation.TargetFileValidator(
                {
                    "Target-File": "Dockerfile"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_target_file_not_string(self):
        self.assertFalse(
            schema_validation.TargetFileValidator(
                {
                    FieldKeys.TARGET_FILE: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
