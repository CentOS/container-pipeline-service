from ci.tests.test_00_unit.test_05_index_ci.indexcibase import IndexCIBase, \
    DUMMY_INDEX_FILE
from ci.container_index.lib.constants import *
import ci.container_index.lib.checks.value_validation as value_validation
import ci.container_index.lib.state as index_ci_state


class CccpYamlExistsValidationTests(IndexCIBase):

    def test_00_setup_test(self):
        self._setup_test()