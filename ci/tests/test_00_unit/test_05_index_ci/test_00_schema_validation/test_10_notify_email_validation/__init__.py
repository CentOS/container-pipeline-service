from ci.tests.test_00_unit.test_05_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class NotifyEmailValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_validation_succeeds_valid_notify_email(self):
        self.assertTrue(
            schema_validation.NotifyEmailValidator(
                {
                    FieldKeys.NOTIFY_EMAIL: "test@example.com"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_02_validation_fails_missing_notify_email(self):
        self.assertFalse(
            schema_validation.NotifyEmailValidator(
                {
                    "Notify-Email": "test@example.com"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_validation_fails_notify_email_not_string(self):
        self.assertFalse(
            schema_validation.NotifyEmailValidator(
                {
                    FieldKeys.NOTIFY_EMAIL: 1
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
