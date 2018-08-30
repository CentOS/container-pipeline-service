#!/usr/bin/env python2
# -*- coding: utf_8 -*-

import unittest

from ccp.notifications import notify


class TestNotify(unittest.TestCase):
    """
    Test Notify class responsible for notifying
    user with build status and details.
    """

    def setUp(self):
        self.notify_obj = notify.BuildNotify()

    def test_subject_of_email(self):
        """
        Notitications: Tests processing subject of email
        """
        job = "ccp-a-b-c"

        # Check the SUCCESS case
        self.assertEqual(
            self.notify_obj.subject_of_email(
                True, job),
            "[registry.centos.org] SUCCESS: Container build {}".format(
                job))

        # Check the FAILED case
        self.assertEqual(
            self.notify_obj.subject_of_email(
                False, job),
            "[registry.centos.org] FAILED: Container build {}".format(
                job))

    def test_body_of_email(self):
        """
        Notifications: Tests processing body of email
        """

        # check the SUCCESS case
        status = "Success"
        repository = "registry.centos.org/foo/bar"
        cause = "Started by admin"
        expected_value = """\
Build Status:                 Success
Repository:                   registry.centos.org/foo/bar
Cause of build:               Started by admin

--
Do you have a query?
Talk to Pipeline team on #centos-devel at freenode
CentOS Community Container Pipeline Service
https://wiki.centos.org/ContainerPipeline
https://github.com/centos/container-index
"""

        self.assertEqual(
            self.notify_obj.body_of_email(
                status,
                repository,
                cause),
            expected_value)


if __name__ == "__main__":
    unittest.main()
