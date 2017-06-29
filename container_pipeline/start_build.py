import logging
import os
import sys
import json

from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.queue import JobQueue
from container_pipeline.lib import settings
import container_pipeline.utils as utils


def build(appid, jobid, repo_url, repo_branch, repo_build_path, target_file,
          notify_email, desired_tag, depends_on, test_tag):
    job_name = utils.get_job_name({
        'appid': appid, 'jobid': jobid, 'desired_tag': desired_tag})
    project = utils.get_job_hash(job_name)
    openshift = Openshift(logger=logger)
    try:
        openshift.create(project)
    except OpenshiftError:
        pass
    openshift.clean_project(project)
    template_path = os.path.join(
        os.path.dirname(__file__), 'template.json')
    try:
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
    except OpenshiftError:
        pass
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
    }))


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('console')
    (appid, jobid, repo_url, repo_branch, repo_build_path,
     target_file, notify_email, desired_tag, depends_on,
     test_tag) = sys.argv[1:]
    build(*sys.argv[1:])
