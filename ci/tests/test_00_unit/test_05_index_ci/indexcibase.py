from os import path

from ci.tests.base import BaseTestCase
import ci.container_index.lib.state as index_ci_state

SETUP_PACKAGES = False
DUMMY_INDEX_FILE = "./test.yaml"


class IndexCIBase(BaseTestCase):

    node = "controller"

    @staticmethod
    def _print_init_msg(msg):
        count = len(msg)
        print("\n")
        print("=" * count)
        print(msg)
        print("=" * count)

    def _setup_test(self):
        """Setup the requirements for test"""
        # Setup node info
        if SETUP_PACKAGES:
            self.run_cmd("sudo yum -y install epel-release", stream=True)
            self.run_cmd("sudo yum -y install PyYAML python-networkx",
                         stream=True)
        self.setUp()
