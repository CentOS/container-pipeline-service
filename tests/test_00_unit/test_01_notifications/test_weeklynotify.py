#!/usr/bin/env python2
# -*- coding: utf_8 -*-

import unittest

from ccp.notifications import weeklynotify


class TestWeeklyNotify(unittest.TestCase):
    """
    Tests WeeklyNotify class, responsible for notifying
    users about weekly scan status.
    """

    def setUp(self):
        self.notify_obj = weeklynotify.WeeklyScanNotify()

    def test_body_of_email(self):
        """
        Notifications.Weekly: Tests processing body of email
        """

        status = True
        repository = "https://registry.centos.org/foo/bar"
        expected_value = """\
Scan status:                  Success
Repository:                   https://registry.centos.org/foo/bar

--
Do you have a query?
Talk to CentOS Container Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline
"""
        self.assertEqual(
            self.notify_obj.body_of_email(
                status,
                repository),
            expected_value)

    def test_image_absent_email_body(self):
        """
        Notifications.Weekly: Tests email body for image absent case
        """
        expected_value = """\
Scan status:                  Image is absent in the registry, scan is aborted.

--
Do you have a query?
Talk to CentOS Container Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline
"""
        self.assertEqual(
            self.notify_obj.image_absent_email_body(),
            expected_value)


if __name__ == "__main__":
    unittest.main()
