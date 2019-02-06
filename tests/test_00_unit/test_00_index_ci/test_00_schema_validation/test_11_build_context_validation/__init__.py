from ci.tests.test_00_unit.test_00_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class BuildContextValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_build_context(self):
        self.assertTrue(
            schema_validation.BuildContextValidator(
                {
                    FieldKeys.BUILD_CONTEXT: "."
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_build_context(self):
        self.assertFalse(
            schema_validation.BuildContextValidator(
                {
                    "Build-Context": "."
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_build_context_not_string(self):
        self.assertFalse(
            schema_validation.BuildContextValidator(
                {
                    FieldKeys.BUILD_CONTEXT: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
