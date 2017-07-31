#!/usr/bin/python

import json
import os

from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue

import utils


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

    lint_job_data = {}

    try:
        dockerfile_location = \
            os.path.join(os.environ['DOCKERFILE_DIR'], git_path, filename)
        with open(dockerfile_location) as f:
            dockerfile = f.read()
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
            "build_status": False
        }

        queue.put(json.dumps(response), tube="master_tube")
        print "==>Put job on 'master_tube' tube"
        return False
    else:
        lint_job_data = {
            "appid": appid,
            "job_name": job_name,
            "dockerfile": dockerfile,
            "notify_email": notify_email,
            "logs_dir": logs_dir,
            "action": "start_linter",
            "jobid": jobid,
            "repo_url": repo_url,
            "repo_branch": repo_branch,
            "repo_build_path": repo_build_path,
            "target_file": target_file,
            "desired_tag": desired_tag,
            "depends_on": depends_on,
            "test_tag": test_tag
        }

        queue.put(json.dumps(lint_job_data), tube="master_tube")
        return True
