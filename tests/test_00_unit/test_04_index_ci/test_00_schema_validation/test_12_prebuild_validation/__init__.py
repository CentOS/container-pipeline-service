from tests.test_00_unit.test_04_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class PrebuildValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_succeeds_no_prebuild_script(self):
        self.assertTrue(
            schema_validation.PrebuildValidator(
                {
                    "Prebuild-Script": "test.sh"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_succeeds_both_prebuild_script_prebuild_context_present(self):
        self.assertTrue(
            schema_validation.PrebuildValidator(
                {
                    FieldKeys.PREBUILD_SCRIPT: "/test.sh",
                    FieldKeys.PREBUILD_CONTEXT: "."
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_fails_prebuild_script_present_prebuild_context_missing(self):
        self.assertFalse(
            schema_validation.PrebuildValidator(
                {
                    FieldKeys.PREBUILD_SCRIPT: "/test.sh",
                    "Prebuild-Context": "."
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
