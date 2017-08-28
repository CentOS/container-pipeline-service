import logging
import os
import sys
import time

from container_pipeline.lib.log import load_logger
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from trigger_dockerfile_lint import trigger_dockerfile_linter
from container_pipeline.utils import get_project_name, get_job_hash


def create_new_job():
    """
    Creates new job (a dictionary) with default value as `None` for all the
    keys. This is the central place for creation of a job for container
    pipeline service
    """
    job = dict.fromkeys([
        "project_name",  # centos/centos:latest will be centos-centos-latest
        "notify_email",  # email to send notifications to
        "depends_on",    # parent image. Rebuild of parent will cause child to
                         # rebuild as well
        "repo_branch",   # branch of the repository to checkout
        "logs_dir",      # directory where all workers' logs files will be
                         # stored
        "test_tag",      # temporary tag to be applied to image
        "repo_url",      # url of the remote git repository to build
        "repo_build_path",  # path on the repo where Dockerfile can be found
        "target_file",   # Name of the Dockerfile to use to build container
                         # image
        "jobid",         # equivalent to image name in Docker hub lingo
        "desired_tag",   # tag to be applied to the image
        "appid",         # equivalent to namespacein Docker hub lingo
        "action",        # action to be performed (lint, build, scan, etc.)
        "dockerfile",    # contents of the Dockerfile for linter purpose
        "job_name",      # same as project_name. need to remove
        "output_image",  # full path to the built image
        "namespace",     # again same as project_name & job_name. need to
                         # remove
        "image_name",    # <appid>/<jobid>:<desired_tag>
        "logs_URL",      # https URL for the logs hosted on nginx
        "logs_file_path",   # path to the logs of all scanners
        "build_status",  # status of build process
        "lint_status",   # status of lint process
        "scan_status",   # status of scan process
        "delivery_status",   # status of delivery process
        "project_hash_key",  # hash value of `project_name` key
        # retry params for build worker to retry builds if required
        "retry",
        "retry_delay",
        "last_run_timestamp",
        # params specific to test worker
        "image_under_test",  # image being tested
        # TODO: this needs to go away
        "beanstalk_server"   # beanstalk server to connect to
    ])

    return job


def create_project(job):
    # job_name = utils.get_job_name({
    #     'appid': appid, 'jobid': jobid, 'desired_tag': desired_tag})
    # project = utils.get_job_hash(job_name)
    openshift = Openshift(logger=logger)
    try:
        openshift.login("test-admin", "test")
        if openshift.get_project(job["project_hash_key"]):
            openshift.delete(job["project_hash_key"])
            time.sleep(50)
        openshift.create(job["project_hash_key"])
    except OpenshiftError:
        try:
            openshift.delete(job["project_hash_key"])
        except OpenshiftError as e:
            logger.error(e)
        raise

    template_path = os.path.join(
        os.path.dirname(__file__), 'template.json')
    openshift.upload_template(job["project_hash_key"], template_path, {
        'SOURCE_REPOSITORY_URL': job["repo_url"],
        'REPO_BRANCH': job["repo_branch"],
        'APPID': job["appid"],
        'JOBID': job["jobid"],
        'REPO_BUILD_PATH': job["repo_build_path"],
        'TARGET_FILE': job["target_file"],
        'NOTIFY_EMAIL': job["notify_email"],
        'DESIRED_TAG': job["desired_tag"],
        'TEST_TAG': job["test_tag"]
    })


def main(args):
    # create new job
    job = create_new_job()

    (appid, jobid, repo_url, repo_branch, repo_build_path,
     target_file, notify_email, desired_tag, depends_on,
     test_tag) = args

    # having '/' in a value used in os.path.join generates unexpected paths
    if repo_build_path.startswith("/"):
        repo_build_path = repo_build_path[1:]

    if target_file.startswith("/"):
        target_file = target_file[1:]

    # populate job's keys with appropriate values
    job["appid"] = appid
    job["notify_email"] = notify_email
    job["logs_dir"] = '/srv/pipeline-logs/{}'.format(test_tag)
    job["action"] = "start_linter"
    job["jobid"] = jobid
    job["repo_url"] = repo_url
    job["repo_branch"] = repo_branch
    job["repo_build_path"] = repo_build_path
    job["target_file"] = target_file
    job["desired_tag"] = desired_tag
    job["depends_on"] = depends_on
    job["test_tag"] = test_tag

    job["project_name"] = get_project_name(job)
    job["namespace"] = job["project_name"]
    job["project_hash_key"] = get_job_hash(job["project_name"])
    job["job_name"] = job["project_name"]

    try:
        linter_status = trigger_dockerfile_linter(job)
        if linter_status:
            create_project(job)
    except OpenshiftError:
        sys.exit(1)


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('jenkins')
    main(sys.argv[1:])
