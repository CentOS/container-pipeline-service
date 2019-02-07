from os import path

from tests.base import BaseTestCase
import ci.container_index.lib.state as index_ci_state

SETUP_PACKAGES = False
DUMMY_INDEX_FILE = "./test.yaml"


class IndexCIBase(BaseTestCase):

    node = "controller"

    def _setup_test(self):
        """Setup the requirements for test"""
        # Setup node info
        if SETUP_PACKAGES:
            self.run_cmd("sudo yum -y install epel-release", stream=True)
            self.run_cmd("sudo yum -y install PyYAML python-networkx",
                         stream=True)
        self.setUp()
