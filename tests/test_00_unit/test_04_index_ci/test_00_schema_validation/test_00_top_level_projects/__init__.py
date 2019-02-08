from tests.test_00_unit.test_04_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.schema_validation as schema_validation


class ProjectsValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()

    def test_01_top_level_validator_success_valid_projects_list(self):
        self.assertTrue(
            schema_validation.TopLevelProjectsValidator(
                {
                    FieldKeys.PROJECTS: [
                        1, 2
                    ]
                },
                DUMMY_INDEX_FILE
            )
        )

    def test_02_top_level_validator_fails_missing_project(self):
        self.assertFalse(
            schema_validation.TopLevelProjectsValidator(
                {
                    "Prj": [
                        1, 2
                    ]
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )

    def test_03_top_level_validator_fails_projects_not_list(self):
        self.assertFalse(
            schema_validation.TopLevelProjectsValidator(
                {
                    FieldKeys.PROJECTS: "Ramu"
                },
                DUMMY_INDEX_FILE
            ).validate().success
        )
