from ci.tests.base import BaseTestCase
from ci.lib import _print, request_json
from container_pipeline.utils import get_project_name_with_params


class ApiTestCase(BaseTestCase):

    def setUpAPITests(self):
        super(ApiTestCase, self)
        self.setUp()
        self.app_id = "test"
        self.job_id = "test"
        self.desired_tag = "test"
        self.git_url = "http://github.com/some/repo"
        self.git_path = "/"
        self.git_branch = "master"
        self.target_file = "Dockerfile"
        self.test_tag = "TEST"
        self.build_context = "./"
        self.depends_on = "centos/centos:latest"
        self.notify_email = "container-status-report@centos.org"
        self.logs_dir = "/srv/pipeline-logs/" + self.test_tag
        self.provision()
        run_host = self.hosts['jenkins_slave']
        self.run_host = run_host['host']
        self.run_host_key = run_host['private_key']
        self.run_host_user = run_host['remote_user']
        self.config_endpoints()

    def config_endpoints(self):
        self.api_endpoint = str.format(
            "http://{endpoint}:{port}/api/{apiversion}",
            endpoint=self.run_host,
            port="9000",
            apiversion="v1"
        )
        self.projects_endpoint = str.format(
            "{apiendpoint}/projects/?format=json",
            self.api_endpoint
        )

    def run_dj_script(self, script):
        _script = (
            'import os, django;'
            'os.environ.setdefault(\\"DJANGO_SETTINGS_MODULE\\", '
            '\\"container_pipeline.lib.settings\\"); '
            'django.setup(); '
            'from container_pipeline.models.pipeline import Project, Build, \\'
            'BuildPhase;'
            '{}'
        ).format(script)
        return self.run_cmd(
            'cd /opt/cccp-service && '
            'python -c "{}"'.format(_script),
            host=self.run_host,
            user=self.run_host_user
        )

    def test_00_setup_database(self):
        _print("Setting up for tests...")
        self.setUpAPITests()

    def test_01_project_created_matches_in_api(self):
        _print("Test if created project details are retrieved correctly by API")
        self.project_name = get_project_name_with_params(
            self.app_id,
            self.job_id,
            self.desired_tag
        )

        # Create project data entry for test project
        script = str.format(
            "p, c = Project.objects.get_or_create(name={})",
            self.project_name
        )
        self.run_dj_script(script)

        # get data from api end point now
        api_data = request_json(
            str.format(
                "{endpoint}&project={project}",
                endpoint=self.projects_endpoint,
                project=self.project_name
            )
        )

        self.assertIsNotNone(api_data)
        found = False
        if api_data:
            for p in api_data["results"]:
                if self.project_name == p["name"]:
                    found = True
        self.assertTrue(found)

