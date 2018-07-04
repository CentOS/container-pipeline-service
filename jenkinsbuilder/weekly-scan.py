#!/usr/bin/env python

"""
moduleauthor: The Container Pipeline Service Team

This module iniializes the weekly scan by finding out the list of images
on the registry and initializing the scan tasks for the workers.
"""

import beanstalkc
import container_pipeline.lib.dj
from container_pipeline.models.pipeline import Project, Build, BuildPhase
from django.utils import timezone
import glob
import json
import os
import subprocess
import sys
import uuid
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
# str_catalog = subprocess.check_output(
#    ["curl", "%s:5000/v2/_catalog" % registry]
# )

# convert string into a list to use for comparison
# json_catalog = json.loads(str_catalog).values()[0]

# have a list of files in the index_dir
files = glob.glob("%s/*.y*ml" % index_dir)

# index dir will always have yml files only; but just in case
# for f in files:
#    if f.endswith(".yml"):
#        continue
#    files.remove(f)

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

        project_name = "{}-{}-{}".format(app_id, job_id, desired_tag)

        try:
            project = Project.objects.get(name=project_name)
        except Project.DoesNotExist:
            print ("Skipping {}, as its not found in database.".format(
                project_name))
            continue

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
        job_uuid = str(uuid.uuid4())
        data = {
            "action": "start_scan",
            "tag": desired_tag,
            "project_name": project_name,
            "namespace": project_name,
            "image_under_test": "%s:5000/%s/%s:%s" %
                                (registry, app_id, job_id, desired_tag),
            "output_image": "registry.centos.org/%s/%s:%s" %
                            (app_id, job_id, desired_tag),
            "notify_email": email,
            "weekly": True,
            "logs_dir": LOGS_DIR,
            "test_tag": test_tag,
            "job_name": job_id,
            "uuid": job_uuid
        }

        job = bs.put(json.dumps(data))

        build = Build.objects.create(
            uuid=job_uuid,
            project=project,
            status='queued',
            start_time=timezone.now(),
            weekly_scan=True
        )
        scan_phase, created = BuildPhase.objects.get_or_create(
            build=build,
            phase='scan'
        )
        scan_phase.status = 'queued'
        scan_phase.save()

        entry_short_name = str(app_id) + "/" + str(job_id)

        print "Image %s sent for weekly scan with data %s" % \
              (entry_short_name, data)
