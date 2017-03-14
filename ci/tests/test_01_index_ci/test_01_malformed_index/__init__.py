from ci.tests.test_01_index_ci.index_ci_base import IndexCIBase, config


class MalformedIndexTester(IndexCIBase):
    _test_index_location = IndexCIBase._base_test_dir + "/" + config["tests"]["1"] + "/" + config["test_index"] + "/"

    def test_00_fails_missing_id(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if id field is missing in index",
                                            self._test_index_location + "test_00")[0])
        print("VERIFIED")

    def test_01_fails_duplicate_id_in_index(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has duplicate id",
                                            self._test_index_location + "test_01")[0])
        print("VERIFIED")

    def test_02_fails_missing_app_id(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has a missing app-id",
                                            self._test_index_location + "test_02")[0])
        print("VERIFIED")

    def test_03_fails_missing_job_id(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has a missing job-id",
                                            self._test_index_location + "test_03")[0])
        print("VERIFIED")

    def test_04_fails_missing_git_url(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has a missing git-url",
                                            self._test_index_location + "test_04")[0])
        print("VERIFIED")

    def test_05_fails_missing_git_path(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has a missing git-path",
                                            self._test_index_location + "test_05")[0])
        print("VERIFIED")

    def test_06_fails_missing_target_file(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has a missing target-file",
                                            self._test_index_location + "test_06")[0])
        print("VERIFIED")

    def test_07_fails_missing_desired_tag(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has missing desired-tag",
                                            self._test_index_location + "test_06")[0])
        print("VERIFIED")

    def test_08_fails_missing_notify_email(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has missing notify-email",
                                            self._test_index_location + "test_07")[0])
        print("VERIFIED")

    def test_09_fails_missing_depends_on(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if index has missing depends-on",
                                            self._test_index_location + "test_09")[0])
        print("VERIFIED")

    def test_10_fails_git_url_endswith_dotgit(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if git url ends with .git",
                                            self._test_index_location + "test_10")[0])
        print("VERIFIED")
