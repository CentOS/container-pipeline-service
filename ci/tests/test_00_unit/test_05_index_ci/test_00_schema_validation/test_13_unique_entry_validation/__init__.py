from ci.tests.test_00_unit.test_05_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation
import ci.container_index.lib.state as index_ci_state


class PrebuildValidationTests(IndexCIBase):

    def _validate_entries(self, entries, index_file):
        s = index_ci_state.State()
        for e in entries:
            if CheckKeys.STATE not in e:
                e[CheckKeys.STATE] = s
            if not schema_validation.UniqueEntryValidator(
                    e,
                    index_file
            ).validate().success:
                return False
        return True

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_succeeds_all_keys_unique(self):
        self.assertTrue(
            self._validate_entries(
                [
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test1",
                        FieldKeys.DESIRED_TAG: "v1"
                    },
                    {
                        FieldKeys.ID: 2,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test2",
                        FieldKeys.DESIRED_TAG: "v2"
                    }
                ],
                DUMMY_INDEX_FILE
            )
        )

    def test_02_succeeds_job_id_same_desired_tag_different(self):
        self.assertTrue(
            self._validate_entries(
                [
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test",
                        FieldKeys.DESIRED_TAG: "v1"
                    },
                    {
                        FieldKeys.ID: 2,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test",
                        FieldKeys.DESIRED_TAG: "v2"
                    }
                ],
                DUMMY_INDEX_FILE
            )
        )

    def test_03_succeeds_job_id_different_tag_matches(self):
        self.assertTrue(
            self._validate_entries(
                [
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test1",
                        FieldKeys.DESIRED_TAG: "v1"
                    },
                    {
                        FieldKeys.ID: 2,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test2",
                        FieldKeys.DESIRED_TAG: "v1"
                    }
                ],
                DUMMY_INDEX_FILE
            )
        )

    def test_04_fails_id_same(self):
        self.assertFalse(
            self._validate_entries(
                [
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test1",
                        FieldKeys.DESIRED_TAG: "v1"
                    },
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test2",
                        FieldKeys.DESIRED_TAG: "v2"
                    }
                ],
                DUMMY_INDEX_FILE
            )
        )

    def test_05_fails_app_id_job_id_desired_tag_same(self):
        self.assertFalse(
            self._validate_entries(
                [
                    {
                        FieldKeys.ID: 1,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test",
                        FieldKeys.DESIRED_TAG: "v1"
                    },
                    {
                        FieldKeys.ID: 2,
                        FieldKeys.APP_ID: "test",
                        FieldKeys.JOB_ID: "test",
                        FieldKeys.DESIRED_TAG: "v1"
                    }
                ],
                DUMMY_INDEX_FILE
            )
        )
