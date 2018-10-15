# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from ccp_server.models.status import Status  # noqa: E501
from ccp_server.test import BaseTestCase


class TestInfraController(BaseTestCase):
    """InfraController integration test stubs"""

    def test_liveness(self):
        """Test case for liveness

        Get the liveness of API service
        """
        response = self.client.open(
            '/api/v1//liveness',
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
