#!/usr/bin/env python

import beanstalkc
import glob
import json
import os
import subprocess
import sys
import yaml


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

        entry_short_name = app_id + "/" + job_id

        # Scan an image only if it exists in the catalog!
        if entry_short_name in json_catalog:
            data = {
                "action": "start_scan",
                "tag": desired_tag,
                "name_space": app_id + "-" + job_id + "-" + desired_tag,
                "name": "%s:5000/%s/%s:%s" %
                (registry, app_id, job_id, desired_tag),
                "notify_email": email,
                "weekly": True
            }

            job = bs.put(json.dumps(data))
            print "Image %s sent for weekly scan with data %s" % \
                (entry_short_name, data)
