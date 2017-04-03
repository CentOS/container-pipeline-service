#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting build details from jenkins"
build_details = {}
build_details["action"] = "start_build"
build_details["appid"] = sys.argv[1]
build_details["jobid"] = sys.argv[2]
build_details["desired_tag"] = sys.argv[3]
build_details["repo_branch"] = sys.argv[4]
build_details["repo_build_path"] = sys.argv[5]
build_details["target_file"] = sys.argv[6]
build_details["notify_email"] = sys.argv[7]
build_details["depends_on"] = sys.argv[8]
build_details["logs_dir"] = sys.argv[9]
build_details["TEST_TAG"] = sys.argv[10]

print "Pushing bild details in the tube"
bs = beanstalkc.Connection(host="BEANSTALK_SERVER")
bs.use("master_tube")
bs.put(json.dumps(build_details))
print "build details is pushed to master tube"
