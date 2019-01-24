from ci.tests.test_00_unit.test_00_index_ci.indexcibase import IndexCIBase
import ci.container_index.lib.state as index_ci_state
from uuid import uuid4
from os import path, mkdir, utime


class FilesBaseTest(IndexCIBase):

    def setup_mock_location(self, file_names):
        s = index_ci_state.State()
        mock_loc = path.join(s.state_mock, str(uuid4()))
        if not path.exists(mock_loc):
            mkdir(mock_loc)
        for f, d in file_names.iteritems():
            p = path.join(mock_loc, f)
            if not d:
                with open(p, "a"):
                    utime(p, None)
            else:
                with open(p, "w+") as fl:
                    fl.write(d)
        return s, mock_loc
