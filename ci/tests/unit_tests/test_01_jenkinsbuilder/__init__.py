from ci.tests.base import BaseTestCase
import jenkinsbuilder.cccp_index_reader as cccp_index_reader
from os import path
import yaml


def _print_test_msg(msg):
    print "=" * len(msg)
    print msg
    print "=" * len(msg)


class Test01IndexReader(BaseTestCase):

    def test_00_projectify_correctly_all_fields(self):
        _print_test_msg("Test if a project is projectified correctly if all parameters are populated")
        new_proj = [{'project': {}}]
        app_id = "test1"
        job_id = "project1"
        git_url = "https://github.com/mohammedzee1000/container-pipeline-service-indexci-testprojects"
        git_path = "projects/baseproject/project1"
        git_branch = "master"
        target_file = "Dockerfile"
        desired_tag = "latest"
        notify_email = "mohammed.zee1000@gmail.com"
        depends_on_jobs = "foo/bar:latest,foo/bar:latest1"
        depends_on = ["foo/bar:latest", "foo/bar:latest1"]
        rel_path = "/" + git_path

        resultset = cccp_index_reader.projectify(new_proj, app_id, job_id, git_url, git_path, git_branch, target_file,
                                                 depends_on_jobs, depends_on, notify_email, desired_tag)

        self.assertTrue(resultset[0]["project"]["appid"] == app_id and resultset[0]["project"]["jobid"] == job_id and
                        resultset[0]["project"]["name"] == app_id and resultset[0]["project"]["git_url"] == git_url and
                        resultset[0]["project"]["git_branch"] == git_branch and resultset[0]["project"]["rel_path"] == rel_path and
                        resultset[0]["project"]["target_file"] == target_file and resultset[0]["project"]["depends_on"] == depends_on_jobs and
                        resultset[0]["project"]["notify_email"] == notify_email and resultset[0]["project"]["desired_tag"] == desired_tag and
                        resultset[0]["project"]["jobs"] == ['cccp-rundotsh-job'] and resultset[0]["project"]["rundotshargs"] == ""
                        )

    def test_01_main_creates_jjb_file_correct_data(self):
        _print_test_msg("Test if main creates jjb_fileif correct data is given")
        index_location = path.dirname(path.realpath(__file__)) + "/test_index"
        data = cccp_index_reader.main(index_location, mock=True)
        self.assertTrue(path.exists(data[0]["dump_file"]))

    def test_02_main_file_data_matches_info(self):
        _print_test_msg("Test if project data in file matches the information in index file")
        index_location = path.dirname(path.realpath(__file__)) + "/test_index"
        data = cccp_index_reader.main(index_location, mock=True)
        proj_info = data[0]["project_info"]
        dump_file = data[0]["dump_file"]
        with open(dump_file, "r") as f:
            file_data = yaml.load(f)
            self.assertTrue(proj_info == file_data)