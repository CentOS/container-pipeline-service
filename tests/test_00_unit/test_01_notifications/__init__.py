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
        self.image_name = "a/b:c"
        self.registry_url = "registry.centos.org"
        self.registry_alias = "null"

    def test_subject_of_email_1(self):
        """
        Notitications: Tests subject success case registry without port
        """
        # Check the SUCCESS case
        self.assertEqual(
            self.notify_obj.subject_of_email(
                True,
                self.image_name,
                self.registry_url,
                self.registry_alias),
            "[{}] SUCCESS: Container build {}".format(
                self.registry_url,
                self.image_name))

    def test_subject_of_email_2(self):
        """
        Notitications: Tests subject success case registry with port
        """
        # case for registry name with port
        self.registry = "registry.centos.org:5000"

        # Check the SUCCESS case
        self.assertEqual(
            self.notify_obj.subject_of_email(
                True, self.image_name, self.registry,
                self.registry_alias),
            # using registry name without port
            "[registry.centos.org] SUCCESS: Container build {}".format(
                self.image_name))

    def test_subject_of_email_3(self):
        """
        Notitications: Tests subject failure case
        """
        # Check the FAILED case
        self.assertEqual(
            self.notify_obj.subject_of_email(
                False,
                self.image_name,
                self.registry_url,
                self.registry_alias),
            "[{}] FAILED: Container build {}".format(
                self.registry_url,
                self.image_name))

    def test_body_of_email(self):
        """
        Notifications: Tests processing body of email
        """

        # check the SUCCESS case
        status = "Success"
        cause = "Started by admin"
        expected_value = """\
Build Status:                 Success
Repository:                   https://registry.centos.org/a/b
Cause of build:               Started by admin

--
Do you have a query?
Talk to CentOS Container Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline
"""

        self.assertEqual(
            self.notify_obj.body_of_email(
                status,
                self.image_name,
                cause,
                self.registry_url,
                self.registry_alias),
            expected_value)


if __name__ == "__main__":
    unittest.main()
