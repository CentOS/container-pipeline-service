from ci.tests.test_00_unit.test_00_index_ci.index_ci_base import IndexCIBase, config


class DependencyValidateTests(IndexCIBase):
    _test_index_location = IndexCIBase._base_test_dir + "/" + config["tests"]["4"] + "/" + config["test_index"] + "/"

    def test_00_builds_valid_dependency_tree(self):
        data = self._run_index_ci("Test if index ci generates a proper dependency tree.",
                                  self._test_index_location + "test_00")
        success = False
        if data[0]:
            self.dependency_graph = data[2]
            if self.dependency_graph.dependency_exists("test1/project1:latest", "test1/project2:latest") and \
                    self.dependency_graph.dependency_exists("test1/project2:latest", "test1/project3:latest"):
                success = True

        self.assertTrue(success)
        print("VERIFIED")

    def test_01_success_valid_dependency(self):
        self.assertTrue(self._run_index_ci("Test if index ci succeeds if dependencies are ok.",
                                           self._test_index_location + "test_01")[0])
        print("VERIFIED")

    def test_02_fails_cyclic_dependency(self):
        self.assertFalse(self._run_index_ci("Test if index ci fails if dependencies are cyclic.",
                                            self._test_index_location + "test_02")[0])
        print("VERIFIED")
