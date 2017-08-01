import logging
import os
import sys
import time

import container_pipeline.utils as utils
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from trigger_dockerfile_lint import trigger_dockerfile_linter


def create_project(appid, jobid, repo_url, repo_branch, repo_build_path,
                   target_file, notify_email, desired_tag, depends_on,
                   test_tag):
    job_name = utils.get_job_name({
        'appid': appid, 'jobid': jobid, 'desired_tag': desired_tag})
    project = utils.get_job_hash(job_name)
    openshift = Openshift(logger=logger)
    try:
        openshift.login("test-admin", "test")
        if openshift.get_project(project):
            openshift.delete(project)
            time.sleep(50)
        openshift.create(project)
    except OpenshiftError:
        try:
            openshift.delete(project)
        except OpenshiftError as e:
            logger.error(e)
        raise

    template_path = os.path.join(
        os.path.dirname(__file__), 'template.json')
    openshift.upload_template(project, template_path, {
        'SOURCE_REPOSITORY_URL': repo_url,
        'REPO_BRANCH': repo_branch,
        'APPID': appid,
        'JOBID': jobid,
        'REPO_BUILD_PATH': repo_build_path,
        'TARGET_FILE': target_file,
        'NOTIFY_EMAIL': notify_email,
        'DESIRED_TAG': desired_tag,
        'test_tag': test_tag})


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('jenkins')
    (appid, jobid, repo_url, repo_branch, repo_build_path,
     target_file, notify_email, desired_tag, depends_on,
     test_tag) = sys.argv[1:]
    try:
        linter_status = trigger_dockerfile_linter(
            appid, jobid, repo_url, repo_branch,
            repo_build_path, target_file, notify_email,
            desired_tag, depends_on, test_tag)
        if linter_status:
            create_project(appid, jobid, repo_url, repo_branch, repo_build_path,
                           target_file, notify_email, desired_tag, depends_on,
                           test_tag)
    except OpenshiftError:
        sys.exit(1)
