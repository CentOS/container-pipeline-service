from ci.tests.test_00_unit.test_00_index_ci.index_ci_base import IndexCIBase, config


class TestIndexValues(IndexCIBase):
    _test_index_location = IndexCIBase._base_test_dir + "/" + config["tests"]["2"] + "/" + config["test_index"] + "/"

    def test_00_fails_duplicate_entry(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has duplicate entry",
                                            self._test_index_location + "test_00")[0])
        print("VERIFIED")

    def test_01_fails_app_id_mismatch(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if app-id mismatches with file name",
                                            self._test_index_location + "test_01")[0])
        print("VERIFIED")

    def test_02_fails_invalid_git_url(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if specified git-url is invalid",
                                            self._test_index_location + "test_02")[0])
        print("VERIFIED")

    def test_03_fails_invalid_git_branch(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if specified git branch is invalid",
                                            self._test_index_location + "test_03")[0])
        print("VERIFIED")

    def test_04_fails_invalid_git_path(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if specified git path is invalid",
                                            self._test_index_location + "test_04")[0])
        print("VERIFIED")

    def test_05_fails_missing_cccp_yml(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if specified git-path lacks cccp yml file",
                                            self._test_index_location + "test_05")[0])
        print("VERIFIED")
