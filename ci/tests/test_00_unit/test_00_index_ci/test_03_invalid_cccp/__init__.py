from ci.tests.test_00_unit.test_00_index_ci.index_ci_base import IndexCIBase, config


class CccpValidateTests(IndexCIBase):
    _test_index_location = IndexCIBase._base_test_dir + "/" + config["tests"]["3"] + "/" + config["test_index"] + "/"

    def test_00_fails_missing_job_id(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if job id is missing in cccp.yml",
                                            self._test_index_location + "test_00")[0])
        print("VERIFIED")

    def test_01_fails_invalid_test_script(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if test script location is invalid",
                                            self._test_index_location + "test_01")[0])
        print("VERIFIED")

    def test_02_success_valid_test_script(self):
        self.assertTrue(self._run_index_ci("Test if index ci succeeds if test script location is valid",
                                            self._test_index_location + "test_02")[0])
        print("VERIFIED")

    # TODO : add cases for build script invalid, build script valid, delivery script valid and delivery script invalid
