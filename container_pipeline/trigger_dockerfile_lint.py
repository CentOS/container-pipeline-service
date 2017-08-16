#!/usr/bin/python

import json
import os

from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue
from container_pipeline.utils import get_project_name, get_job_hash

import utils


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
        "job_hash_key"   # hash value of `project_name` key
    ])

    return job


def trigger_dockerfile_linter(appid, jobid, repo_url, repo_branch,
                              repo_build_path, target_file, notify_email,
                              desired_tag, depends_on, test_tag):
    queue = JobQueue(
        host=settings.BEANSTALKD_HOST,
        port=settings.BEANSTALKD_PORT,
        sub="master_tube")

    job_name = utils.get_job_name({
        'appid': appid, 'jobid': jobid, 'desired_tag': desired_tag})
    logs_dir = '/srv/pipeline-logs/{}'.format(test_tag)

    # having '/' in a value used in os.path.join generates unexpected paths
    if repo_build_path.startswith("/"):
        git_path = repo_build_path[1:]

    if target_file.startswith("/"):
        filename = target_file[1:]
    else:
        filename = target_file

    # create new job
    job = create_new_job()

    # populate job's keys with appropriate values
    job["appid"] = appid
    job["job_name"] = job_name
    job["notify_email"] = notify_email
    job["logs_dir"] = logs_dir
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
    job["job_hash_key"] = get_job_hash(job["project_name"])

    try:
        dockerfile_location = \
            os.path.join(os.environ['DOCKERFILE_DIR'], git_path, filename)
        with open(dockerfile_location) as f:
            dockerfile = f.read()
        job["dockerfile"] = dockerfile
    except IOError as e:
        print "==> Error opening the file %s" % dockerfile_location
        print "==> Error: %s" % str(e)
        print "==> Sending Dockerfile linter failure email"
        response = {
            "action": "notify_user",
            "namespace": appid,
            "notify_email": notify_email,
            "job_name": job_name,
            "msg": "Couldn't find the Dockerfile at specified git_path",
            "logs_dir": logs_dir,
            "lint_status": False,
            "build_status": False,
            "project_name": get_project_name(job),
            "test_tag": test_tag
        }

        queue.put(json.dumps(response), tube="master_tube")
        print "==>Put job on 'master_tube' tube"
        return False
    except BaseException as e:
        print "==> Encountered unexpected error. Dockerfile lint trigger failed"
        print "==> Error: %s" % str(e)
        print "==> Sending Dockerfile linter failure email"
        response = {
            "action": "notify_user",
            "namespace": appid,
            "notify_email": notify_email,
            "job_name": job_name,
            "msg": "Unexpected error while trigger Dockerfile linter",
            "logs_dir": logs_dir,
            "lint_status": False,
            "build_status": False,
            "project_name": get_project_name(job),
            "test_tag": test_tag
        }

        queue.put(json.dumps(response), tube="master_tube")
        print "==>Put job on 'master_tube' tube"
        return False
    else:
        queue.put(json.dumps(job), tube="master_tube")
        return True
