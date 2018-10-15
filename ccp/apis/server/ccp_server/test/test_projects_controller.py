# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from ccp_server.models.app_id_job_id_tags import AppIdJobIdTags  # noqa: E501
from ccp_server.models.project_metadata import ProjectMetadata  # noqa: E501
from ccp_server.models.target_file import TargetFile  # noqa: E501
from ccp_server.test import BaseTestCase


class TestProjectsController(BaseTestCase):
    """ProjectsController integration test stubs"""

    def test_project_desired_tags(self):
        """Test case for project_desired_tags

        Get tags for given $app_id/$job_id with build status and image
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tags'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_project_metadata(self):
        """Test case for project_metadata

        Get the metadata of the given project
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag/{desired_tag}/metadata'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_project_target_file(self):
        """Test case for project_target_file

        Get Dockerfile for given project
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/app-id/{app_id}/job-id/{job_id}/desired-tag/{desired_tag}/target-file'.format(namespace='namespace_example', app_id='app_id_example', job_id='job_id_example', desired_tag='desired_tag_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
