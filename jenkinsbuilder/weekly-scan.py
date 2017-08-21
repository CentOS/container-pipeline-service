#!/usr/bin/env python

import beanstalkc
import glob
import json
import os
import subprocess
import sys
import yaml


# Logs base URL
LOGS_DIR_BASE = "/srv/pipeline-logs/"

# connect to beanstalkd tube
bs = beanstalkc.Connection("BEANSTALK_SERVER")
bs.use("master_tube")

# registry server value to be replaced by ansible
registry = "JENKINS_SLAVE"

# cli argument pointing to directory containing yml files
index_dir = sys.argv[1]

# string representation of the catalog on r.c.o
str_catalog = subprocess.check_output(
    ["curl", "%s:5000/v2/_catalog" % registry]
)

# convert string into a list to use for comparison
json_catalog = json.loads(str_catalog).values()[0]

# have a list of files in the index_dir
files = glob.glob("%s/*.yml" % index_dir)

# index dir will always have yml files only; but just in case
for f in files:
    if f.endswith(".yml"):
        continue
    files.remove(f)

# parse the yml file
for f in files:
    with open(os.path.join(os.environ.get("CWD"), "index.d", f)) as stream:
        try:
            yaml_parse = yaml.load(stream)
        except yaml.YAMLError as e:
            print e

    # all entries in a yml file in list of dictionaries format
    entries = yaml_parse.values()[0]

    for entry in entries:
        app_id = entry["app-id"]
        job_id = entry["job-id"]
        desired_tag = entry["desired-tag"]
        email = entry["notify-email"]

        entry_short_name = str(app_id) + "/" + str(job_id)

        # test_tag generation, unique per project
        task = subprocess.Popen(
            "date +%s%N | md5sum | base64 | head -c 14",
            shell=True,
            stdout=subprocess.PIPE)
        test_tag = task.stdout.read()

        LOGS_DIR = os.path.join(LOGS_DIR_BASE, test_tag)

        # Create the logs directory
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)

        # Scan an image only if it exists in the catalog!
        if entry_short_name in json_catalog:
            data = {
                "action": "start_scan",
                "tag": desired_tag,
                "namespace": str(app_id) + "-" + str(job_id) + "-" +
                str(desired_tag),
                "image_under_test": "%s:5000/%s/%s:%s" %
                (registry, app_id, job_id, desired_tag),
                "output_image": "registry.centos.org/%s/%s:%s" %
                (app_id, job_id, desired_tag),
                "notify_email": email,
                "weekly": True,
                "logs_dir": LOGS_DIR,
                "test_tag": test_tag,
                "job_name": job_id
            }

            job = bs.put(json.dumps(data))
            print "Image %s sent for weekly scan with data %s" % \
                (entry_short_name, data)
