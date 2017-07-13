from ci.tests.test_00_unit.test_00_index_ci.index_ci_base import IndexCIBase, config


class BasicTests(IndexCIBase):
    _test_index_location = IndexCIBase._base_test_dir + "/" + config["tests"]["0"] + "/" + config["test_index"] + "/"

    def test_00_base_setup(self):

        self._print_init_msg("Do basic setup")
        self._setup_engine_test()
        print("DONE")

    def test_01_succeeds_correct_index(self):
        self.assertTrue(self._run_index_ci("Test if index ci succeeds if correct index and cccp ymls are given",
                                           self._test_index_location + "test_01")[0])
        print("VERIFIED")

    def test_02_succeeds_correct_index_with_numeric(self):
        self.assertTrue(self._run_index_ci("Test if index ci succeeds even if desired-tag is numeric",
                                           self._test_index_location + "test_02")[0])
        print("VERIFIED")

    def test_03_fails_incorrect_index_file_yml(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if the index file has yml errors",
                                            self._test_index_location + "test_03")[0])
        print("VERIFIED")

    def test_04_fails_missing_top_projects(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index file is missing 'Projects:'",
                                            self._test_index_location + "test_04")[0])
        print("VERIFIED")
