import unittest

from ccp import index_reader


class TestProject(unittest.TestCase):
    """
    Test the Project class representing an
    object in container pipeline
    """

    def setUp(self):
        self.entry = {
            "id": "1",
            "app-id": "foo",
            "job-id": "bar",
            "desired-tag": "latest",
            "git-branch": "master",
            "git-url": "https://github.com/someurl",
            "git-path": "foo/",
            "target-file": "Dockerfile",
            "build-context": "./",
            "notify-email": "abc@example/com",
            "depends-on": ["centos/centos:latest", "centos/centos:7"],
            "prebuild-script": "hooks/script.sh",
            "prebuild-context": "/",
        }
        self.namespace = "ccp"

    def test_load_entries(self):
        """
        Tests creating Project class object which loads entries
        """
        obj = index_reader.Project(self.entry, self.namespace)
        self.assertTrue(isinstance(obj, index_reader.Project))

    def test_string_representation(self):
        """
        Test __str__ representation of Project object
        """
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(
            "foo-bar-latest",
            project.__str__()
        )

    def test_replace_dot_slash_colon_(self):
        """
        Test the helper method to replace . / : _ with hyphen
        """
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(
            "a-b-c-d-e",
            project.replace_dot_slash_colon_("a.b/c_d:e")
        )

    def test_process_depends_on(self):
        """
        Tests depends_on field processing and defaults
        """
        # test the default value
        project = index_reader.Project(self.entry, self.namespace)
        # test if multiple/list of depends-on is converted to string
        self.assertIsInstance(
            project.depends_on,
            str
        )

        # test if commas are included with multiple values of depends_on
        self.assertIn(",", project.depends_on)

        # test the actual values
        self.assertEqual(
            "ccp-centos-centos-latest,ccp-centos-centos-7",
            project.depends_on
        )

    def test_process_desired_tag(self):
        """
        Tests desired tag processing and defaults
        """
        # test a custom value
        self.entry["desired-tag"] = "release"
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(project.desired_tag, "release")

        # test empty value
        self.entry["desired-tag"] = ""
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(project.desired_tag, "latest")

    def test_pre_build_script(self):
        """
        Test processing pre_build_script
        """
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(
            "hooks/script.sh", project.pre_build_script)

        # test a None value, in cases where prebuild-script is not specified
        self.entry.pop("prebuild-script")
        project = index_reader.Project(self.entry, self.namespace)
        self.assertIsNone(project.pre_build_script)

    def test_pre_build_context(self):
        """
        Test processing pre_build_context
        """
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual("/", project.pre_build_context)

        # test a None value, in cases where prebuild-context is not specified
        self.entry.pop("prebuild-context")
        project = index_reader.Project(self.entry, self.namespace)
        self.assertIsNone(project.pre_build_context)

    def test_get_pipeline_name(self):
        """
        Test processing pipeline_name based on given values
        """
        project = index_reader.Project(self.entry, self.namespace)
        self.assertEqual(
            "foo-bar-latest",
            project.pipeline_name)


if __name__ == "__main__":
    unittest.main()
