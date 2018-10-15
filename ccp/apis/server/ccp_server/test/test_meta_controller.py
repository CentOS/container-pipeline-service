# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from ccp_server.models.namespaces import Namespaces  # noqa: E501
from ccp_server.models.projects import Projects  # noqa: E501
from ccp_server.test import BaseTestCase


class TestMetaController(BaseTestCase):
    """MetaController integration test stubs"""

    def test_namespace_projects(self):
        """Test case for namespace_projects

        Get all the projects in given namespace
        """
        response = self.client.open(
            '/api/v1//namespace/{namespace}/projects'.format(namespace='namespace_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_namespaces(self):
        """Test case for namespaces

        Get all available namespaces accessible over APIs
        """
        response = self.client.open(
            '/api/v1//namespaces',
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
