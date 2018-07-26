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
        project = index_reader.Project(self.entry, self.namespace)


if __name__ == "__main__":
    unittest.main()
