import json
import os
import unittest

class BaseTestCase(unittest.TestCase):
    """Base test case to extend test cases from"""

    def setUp(self):
        self.hosts = json.loads(os.environ.get('CCCP_CI_HOSTS') or "{}")

