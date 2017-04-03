from os import path

from ci.tests.base import BaseTestCase
from testindex.Engine import Engine

config = {
    "test_index": "test_index",
    "tests": {
        "0": "test_00_basic",
        "1": "test_01_malformed_index",
        "2": "test_02_index_values",
        "3": "test_03_invalid_cccp",
        "4": "test_04_dependency_validation"
    },
    "local_run": False,
    "local_setup": False,
    "verbose": False
}


class IndexCIBase(BaseTestCase):
    _base_test_dir = path.dirname(path.realpath(__file__))
    node = "controller"

    @staticmethod
    def _print_init_msg(msg):
        count = len(msg)
        print("\n")
        print("=" * count)
        print(msg)
        print("=" * count)

    def _setup_engine_test(self):
        """Setup the requirements for test"""
        # Setup node info
        if not config["local_run"]:
            self.setUp()
        elif config["local_setup"]:
            self.run_cmd("sudo yum -y install epel-release", stream=True)
            self.run_cmd("sudo yum -y install PyYAML python-networkx", stream=True)

    def _run_index_ci(self, msg, index_location):
        """Trigger an index ci run on remote machine and get the output for evaluation"""
        self._print_init_msg(msg)
        return Engine(index_path=index_location, verbose=config["verbose"]).run()
