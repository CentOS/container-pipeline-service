import os
from ci.tests.base import BaseTestCase
from container_pipeline.utils import request_url
import json
import uuid


class APITestCase(BaseTestCase):
    """
    Module to test API
    """

    node = "jenkins_slave"
    api_server = "jenkins_slave"
    test_project = {
        "name": "test-project",
        "target_file_link": "test_link",
        "build_uuid": str(uuid.uuid4())
    }
    api_version = "v1"

    def query_api(self, query):
        api_url = str.format(
            "http://{node}:9001/api/{api_version}/{query}",
            node=str(self.hosts[APITestCase.api_server]['host']),
            api_version=str(self.api_version),
            query=str(query)
        )
        response = request_url(api_url)
        if response:
            return json.loads(
                response.read()
            )
        raise Exception(
                str.format(
                    "Could not get data from endpoint {}",
                    api_url
                )
            )
