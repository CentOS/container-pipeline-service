#!/usr/bin/env python2

# This python module defines a BaseNotify class
# to be inheirted by child build and weekly scan classes.
# This is a single place to lookup for formatting of subject
# and email body for notifications email to be sent to users.


class BaseNotify(object):
    """
    BaseNotify class has related common methods and
    initialization for build and weekly scan notification
    classes.
    """

    def __init__(self):
        self.build_success_subj = \
            "[{registry}] SUCCESS: Container build {image_name}"
        self.build_failure_subj = \
            "[{registry}] FAILED: Container build {image_name}"
        # <30 is adding space formatting for aligning the key values
        self.build_success_body = """\
{0:<30}{1}
{2:<30}{3}
{4:<30}{5}"""

        self.build_failure_body = """\
{0:<30}{1}
{2:<30}{3}"""

        self.email_footer = """\
--
Do you have a query?
Talk to CentOS Container Pipeline team on #centos-devel at freenode
https://wiki.centos.org/ContainerPipeline
"""
