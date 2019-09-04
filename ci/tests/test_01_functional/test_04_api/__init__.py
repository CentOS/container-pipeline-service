import os
from ci.tests.test_01_functional.test_04_api.apitest\
 import APITestCase
from container_pipeline.lib import dj
from container_pipeline.models.pipeline import Project,\
    Build, BuildPhase
import json
from django.utils import timezone

class ApiV1TestCase(APITestCase):
    """
    Module to test api v1.
    """

    node = "jenkins_slave"
    api_server = "jenkins_slave"
    test_project = {
        "name": "test-project",
        "target_file_link": "test_link",
        "build_uuid": str(uuid.uuid4())
    }
    api_version = "v1"

    def run_dj_script(self, script):
        _script = (
            'import os, django; '
            'os.environ.setdefault(\\"DJANGO_SETTINGS_MODULE\\", '
            '\\"container_pipeline.lib.settings\\"); '
            'django.setup();'
            'from container_pipeline.models.pipeline import \\'
            'Project, Build, BuildPhase;'
            '{}'
        ).format(script)
        return self.run_cmd(
            'cd /opt/cccp-service && '
            'python -c "{}"'.format(_script))

    def test_00_project_api_data_matches_db(self):
        self.setUp()

        # Create a project in database
        scr = str.format(
            'p = Project.objects.create(name="{p_name}");'
            'p.target_file_link="{p_f_link}";p.save();',
            p_name=self.test_project.get('name'),
            p_f_link=self.test_project.get(
                'target_file_link'
            )
        )

        self.run_dj_script(scr)

        # Get data from api end point

        project_api_endpoint = str.format(
            "projects/?name={}",
            self.test_project.get('name')
        )
        
        res = self.query_api(project_api_endpoint)
        data = res.get('results')

        # Match data for validation
        found = False
        for item in data:
            if item.get('name') == self.test_project.get('name') and \
                item.get('target_file_link') == \
                self.test_project.get('target_file_link'):
                found = True
                break
        self.assertTrue(found)

    def test_01_build_api_data_matches_db(self):
        self.setUp()
        
        # Setup data in db for test

        scr = str.format(
            'from django.utils import timezone'
            'p = Project.objects.get("{p_name}");'
            'b = Build.objects.create(uuid="{p_uuid}\, project=p,'
            'status="queued", weekly_scan=False'
            'start_time=timezone.now())',
            p_name = str(self.test_project.get('name')),
            p_uuid = str(
                self.test_project.get(
                    'build_uuid'
                )
            )
        )

        # Get data from api endpoint
        build_api_endpoint = str.format(
            "builds/?name={}",
            str(self.test_project.get('name'))
        )

        res = self.query_api(build_api_endpoint)
        data = res.get('results')
        found = False
        for item in data:
                if str(item.project) == \
                    self.test_project.get('name')\
                    and str(item.status) == 'queued':
                    found = True
                    break
        self.assertTrue(found)
