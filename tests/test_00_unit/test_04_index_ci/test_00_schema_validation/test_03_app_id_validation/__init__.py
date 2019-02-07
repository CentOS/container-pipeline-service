from tests.test_00_unit.test_04_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class AppIDValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_app_id(self):
        self.assertTrue(
            schema_validation.AppIDValidator(
                {
                    FieldKeys.APP_ID: "test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_app_id(self):
        self.assertFalse(
            schema_validation.AppIDValidator(
                {
                    "App-ID": "test"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_app_id_mismatch_filename(self):
        self.assertFalse(
            schema_validation.AppIDValidator(
                {
                    FieldKeys.APP_ID: "testx"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_04_validation_fails_app_id_not_string(self):
        self.assertFalse(
            schema_validation.AppIDValidator(
                {
                    FieldKeys.APP_ID: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

