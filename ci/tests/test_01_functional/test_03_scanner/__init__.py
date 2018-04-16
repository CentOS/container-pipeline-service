# module to test scanner functionality

import os

from ci.tests.base import BaseTestCase


class TestScanners(BaseTestCase):
    """
    Module to test linter functionalities.
    """
    node = 'scanner'

    def setUp(self):
        """
        Set Up needed environment for testing.
        Initialize the beanstalkd queue with queues respective to linter.
        """
        super(TestScanners, self).setUp()
        self.logs_dir_base = "/srv/pipeline-logs/"
        # find the a logs dir in /srv/pipeline-logs
        self.logs_dir = self.find_a_logs_dir()

    def find_a_logs_dir(self):
        """
        Find a logs dir in /srv/pipeline-logs with `build_logs.txt`
        file in it, this dir will be used to find scanners results
        """
        for dirpath, dirs, files in os.walk(self.logs_dir_base):
            if "build_logs.txt" in files:
                # this dir path contains "build_logs.txt" file
                print "Logs dir is", dirpath
                return dirpath
        # this is going to fail the tests, than erroring out
        print "build_logs.txt is not present in any logs dir."
        print "This implies tests are going to be failed."
        return self.logs_dir_base

    def test_00_rpm_verify_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # get the relevant result file for scanner to be tested
        result_file = os.path.join(
            self.logs_dir,
            "rpm_verify_scanner_results.json")
        self.assertTrue(result_file)

    def test_01_misc_package_updates_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """

        # get the relevant result file for scanner to be tested
        result_file = os.path.join(
            self.logs_dir,
            "misc_package_updates_scanner_results.json")
        self.assertTrue(result_file)

    def test_02_pipeline_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """

        # get the relevant result file for scanner to be tested
        result_file = os.path.join(
            self.logs_dir,
            "pipeline_scanner_results.json")
        self.assertTrue(result_file)

    def test_03_container_capabilities_scanner_results(self):
        """
        Test if scanner is exporting the results as expected.
        """
        # get the relevant result file for scanner to be tested
        result_file = os.path.join(
            self.logs_dir,
            "container_capabilities_scanner_results.json")
        self.assertTrue(result_file)
