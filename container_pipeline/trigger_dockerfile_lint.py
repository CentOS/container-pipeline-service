#!/usr/bin/python

import json
import os
from django.utils import timezone
from container_pipeline.lib import settings
from container_pipeline.lib.queue import JobQueue
from container_pipeline.models import Build, BuildPhase

def trigger_dockerfile_linter(job):
    queue = JobQueue(
        host=settings.BEANSTALKD_HOST,
        port=settings.BEANSTALKD_PORT,
        sub="master_tube")

    try:
        dockerfile_location = \
            os.path.join(
                os.environ['DOCKERFILE_DIR'],
                "" if job["repo_build_path"] == "/" else job["repo_build_path"],
                job["target_file"])
        with open(dockerfile_location) as f:
            dockerfile = f.read()
        job["dockerfile"] = dockerfile
    except IOError as e:
        print "==> Error opening the file %s" % dockerfile_location
        print "==> Error: %s" % str(e)
        print "==> Sending Dockerfile linter failure email"
        # response = {
        #     "action": "notify_user",
        #     "namespace": job["appid"],
        #     "notify_email": job["notify_email"],
        #     "job_name": job["job_name"],
        #     "msg": "Couldn't find the Dockerfile at specified git_path",
        #     "logs_dir": job["logs_dir"],
        #     "lint_status": False,
        #     "build_status": False,
        #     "project_name": job["project_name"],
        #     "test_tag": job["test_tag"]
        # }
        job["action"] = "notify_user"
        job["lint_status"] = False
        job["build_status"] = False
        job["msg"] = "Couldn't find the Dockerfile at specified git_path"

        queue.put(json.dumps(job), tube="master_tube")
        print "==>Put job on 'master_tube' tube"
        return False
    except BaseException as e:
        print e
        print "==> Encountered unexpected error. Dockerfile lint trigger failed"
        print "==> Error: %s" % str(e)
        print "==> Sending Dockerfile linter failure email"
        # response = {
        #     "action": "notify_user",
        #     "namespace": job["appid"],
        #     "notify_email": job["notify_email"],
        #     "job_name": job["job_name"],
        #     "msg": "Unexpected error while trigger Dockerfile linter",
        #     "logs_dir": job["logs_dir"],
        #     "lint_status": False,
        #     "build_status": False,
        #     "project_name": job["project_name"],
        #     "test_tag": job["test_tag"]
        # }
        job["action"] = "notify_user"
        job["lint_status"] = False
        job["build_status"] = False
        job["msg"] = "Unexpected error while trigger Dockerfile linter"

        queue.put(json.dumps(job), tube="master_tube")
        print "==>Put job on 'master_tube' tube"
        return False
    else:
        build = Build.objects.get(uuid=job["uuid"])
        build.status = 'processing'
        build.save()
        BuildPhase.objects.create(
            build=build, phase='dockerlint', status='queued')
        queue.put(json.dumps(job), tube="master_tube")
        return True
