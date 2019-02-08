from os import path

from tests.base import BaseTestCase
import ci.container_index.lib.state as index_ci_state

SETUP_PACKAGES = False
DUMMY_INDEX_FILE = "./test.yaml"


class IndexCIBase(BaseTestCase):

    node = "controller"

    def _setup_test(self):
        self.setUp()
