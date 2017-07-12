import json
import logging
import os
import sys

import container_pipeline.utils as utils
from container_pipeline.lib import settings
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.lib.queue import JobQueue


def create_project(appid, jobid, repo_url, repo_branch, repo_build_path,
                   target_file, notify_email, desired_tag, depends_on,
                   test_tag):
    job_name = utils.get_job_name({
        'appid': appid, 'jobid': jobid, 'desired_tag': desired_tag})
    project = utils.get_job_hash(job_name)
    is_openshift_good = False
    openshift = Openshift(logger=logger)
    try:
        openshift.login("test-admin", "test")
        openshift.create(project)
        openshift.clean_project(project)
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
        'TEST_TAG': test_tag})
    is_openshift_good = True

    if is_openshift_good:
        queue = JobQueue(host=settings.BEANSTALKD_HOST,
                         port=settings.BEANSTALKD_PORT,
                         sub='master_tube',
                         pub='master_tube', logger=logger)
        queue.put(json.dumps({
            'action': 'start_build',
            'appid': appid,
            'jobid': jobid,
            'desired_tag': desired_tag,
            'repo_branch': repo_branch,
            'repo_build_path': repo_build_path,
            'target_file': target_file,
            'notify_email': notify_email,
            'depends_on': depends_on,
            'logs_dir': '/srv/pipeline-logs/{}'.format(test_tag),
            'TEST_TAG': test_tag
        }), 'master_tube')
    else:
        logger.error("Jenkins is not able to setup openshift project")


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('jenkins')
    (appid, jobid, repo_url, repo_branch, repo_build_path,
     target_file, notify_email, desired_tag, depends_on,
     test_tag) = sys.argv[1:]
    try:
        create_project(*sys.argv[1:])
    except OpenshiftError:
        sys.exit(1)
