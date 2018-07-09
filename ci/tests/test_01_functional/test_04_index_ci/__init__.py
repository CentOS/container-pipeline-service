from os import path, mkdir, utime

from ci.tests.base import BaseTestCase
from ci.container_index.lib.utils import load_yaml, dump_yaml
import ci.container_index.lib.state as index_ci_state
from uuid import uuid4
from ci.container_index.lib.constants import *
from ci.container_index.engine import Engine


SETUP_PACKAGES = False


class IndexCITests(BaseTestCase):
    node = "controller"

    def setup_mock_location(self, file_names):
        s = index_ci_state.State()
        mock_loc = path.join(s.state_mock, str(uuid4()))
        mock_indexd_location = path.join(mock_loc, "index.d")
        if not path.exists(mock_loc):
            mkdir(mock_loc)
        if not path.exists(mock_indexd_location):
            mkdir(mock_indexd_location)
        for f, d in file_names.iteritems():
            p = path.join(mock_indexd_location, f)
            if not d:
                with open(p, "a"):
                    utime(p, None)
            else:
                dump_yaml(p, d)
        return s, mock_loc

    def test_00_setup(self):
        """Setup the requirements for test"""
        # Setup node info
        if SETUP_PACKAGES:
            self.run_cmd("sudo yum -y install epel-release", stream=True)
            self.run_cmd("sudo yum -y install PyYAML python-networkx",
                         stream=True)
        self.setUp()

    def test_01_index_ci_success_correct_index(self):
        st, mock_loc = self.setup_mock_location(
            {
                "bamachrn.yaml": {
                    FieldKeys.PROJECTS: [
                        {
                            FieldKeys.ID: 1,
                            FieldKeys.APP_ID: "bamachrn",
                            FieldKeys.JOB_ID: "python",
                            FieldKeys.DESIRED_TAG: "latest",
                            FieldKeys.GIT_URL: "https://github.com/bamachrn/ccc"
                                               "p-python",
                            FieldKeys.GIT_PATH: "demo",
                            FieldKeys.GIT_BRANCH: "master",
                            FieldKeys.TARGET_FILE: "Dockerfile.demo",
                            FieldKeys.NOTIFY_EMAIL: "hello@example.com",
                            FieldKeys.BUILD_CONTEXT: "./",
                            FieldKeys.DEPENDS_ON: "centos/centos:latest"
                        }
                    ]
                }
            }
        )
        s, summary = Engine(index_location=mock_loc, the_state=st).run()
        self.assertTrue(s)

    def test_02_index_ci_fails_incorrect_index(self):
        st, mock_loc = self.setup_mock_location(
            {
                "bamachrn.yaml": {
                    FieldKeys.APP_ID: "bamachrn",
                    FieldKeys.JOB_ID: "python",
                    FieldKeys.DESIRED_TAG: "latest",
                    FieldKeys.GIT_URL: "https://github.com/bamachrn/cccp-python"
                    ,
                    FieldKeys.GIT_PATH: "does_not_exist",
                    FieldKeys.GIT_BRANCH: "master",
                    FieldKeys.TARGET_FILE: "Dockerfile.demo",
                    FieldKeys.NOTIFY_EMAIL: "hello@example.com",
                    FieldKeys.BUILD_CONTEXT: "./",
                    FieldKeys.DEPENDS_ON: "centos/centos:latest"
                }
            }
        )
        s, summary = Engine(index_location=mock_loc, the_state=st).run()
        self.assertFalse(s)

    def test_03_indexci_runs_specific_schema_validators(self):
        st, mock_loc = self.setup_mock_location(
            {
                "bamachrn.yaml": {
                    FieldKeys.PROJECTS: [
                        {
                            FieldKeys.ID: 1,
                            FieldKeys.APP_ID: "bamachrn",
                        }
                    ]
                }
            }
        )
        s, summary = Engine(
            index_location=mock_loc,
            the_state=st,
            schema_validators=["IDValidator", "AppIDValidator"],
            value_validators="None"
        ).run()
        self.assertTrue(s)

    def test_04_indexci_runs_specific_value_validators(self):
        st, mock_loc = self.setup_mock_location(
            {
                "bamachrn.yaml": {
                    FieldKeys.PROJECTS: [
                        {
                            FieldKeys.ID: 1,
                            FieldKeys.APP_ID: "bamachrn",
                            FieldKeys.JOB_ID: "python",
                            FieldKeys.DESIRED_TAG: "latest",
                            FieldKeys.GIT_URL: "https://github.com/bamachrn/ccc"
                                               "p-python1",
                            FieldKeys.GIT_PATH: "demo",
                            FieldKeys.GIT_BRANCH: "master",
                            FieldKeys.TARGET_FILE: "Dockerfile.demo",
                            FieldKeys.NOTIFY_EMAIL: "hello@example.com",
                            FieldKeys.BUILD_CONTEXT: "./",
                            FieldKeys.DEPENDS_ON: "centos/centos:latest"
                        }
                    ]
                }
            }
        )
        s, summary = Engine(
            index_location=mock_loc,
            the_state=st,
            schema_validators="None",
            value_validators=["GitCloneValidator"]
        ).run()
        self.assertFalse(s)
