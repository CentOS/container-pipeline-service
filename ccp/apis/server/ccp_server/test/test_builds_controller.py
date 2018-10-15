# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from ccp_server.models.build_logs import BuildLogs  # noqa: E501
from ccp_server.models.project_builds_info import ProjectBuildsInfo  # noqa: E501
from ccp_server.models.weekly_scan_builds_info import WeeklyScanBuildsInfo  # noqa: E501
from ccp_server.models.weekly_scan_logs import WeeklyScanLogs  # noqa: E501
from ccp_server.test import BaseTestCase


class TestBuildsController(BaseTestCase):
    """BuildsController integration test stubs"""

    def test_project_build_logs(self):
        """Test case for project_build_logs

        Build logs for given build number
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag/{desired_tag}/build/{build}/logs'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example', build='build_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_project_builds(self):
        """Test case for project_builds

        Get all the builds info for given project
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_project_wscan_build_logs(self):
        """Test case for project_wscan_build_logs

        Weekly scan logs for given wscan-build number
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag/{desired_tag}/wscan-build/{build}/logs'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example', build='build_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_project_wscan_builds(self):
        """Test case for project_wscan_builds

        Get all the weekly scan builds info for given project
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag/{desired_tag}/wscan-builds'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
