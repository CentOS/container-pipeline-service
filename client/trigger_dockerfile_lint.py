#!/usr/bin/python

import beanstalkc
import json
import os
import sys

if __name__ == "__main__":
    bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
    bs.use("master_tube")

    namespace = sys.argv[1]
    git_path = sys.argv[2]
    filename = sys.argv[3]
    notify_email = sys.argv[4]
    job_name = sys.argv[5]

    # having '/' in a value used in os.path.join generates unexpected paths
    if git_path.startswith("/"):
        git_path = git_path[1:]

    if filename.startswith("/"):
        filename = filename[1:]

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
            "linter_results": True,
            "action": "notify_user",
            "namespace": namespace,
            "notify_email": notify_email,
            "job_name": job_name,
            "msg": "Couldn't find the Dockerfile at specified git_path"
        }

        jid = bs.put(json.dumps(response))
        print "==>Put job on 'master_tube' tube with id: %d" % jid
    else:
        lint_job_data["namespace"] = namespace
        lint_job_data["job_name"] = job_name
        lint_job_data["dockerfile"] = dockerfile
        lint_job_data["notify_email"] = notify_email
        lint_job_data["action"] = "start_linter"

        bs.put(json.dumps(lint_job_data))
