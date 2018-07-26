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
        Tests creating Project class object which loads
        entries
        """
        index_reader.Project(self.entry, self.namespace)

    def test_desired_tag(self):
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

    def test_depends_on(self):
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


if __name__ == "__main__":
    unittest.main()
