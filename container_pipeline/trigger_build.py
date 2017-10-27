#!/usr/bin/python
"""
Trigger build.

This is for creating openshift projects after job passes the linting.
This also triggers the build after job is created in openshift
"""
import json
import os
import time

from django.utils import timezone

import container_pipeline.utils as utils
from container_pipeline.lib.openshift import Openshift, OpenshiftError
from container_pipeline.models import Build, BuildPhase


def create_project(queue, job, logger):
    job_name = job.get("job_name")
    project_name_hash = utils.get_job_hash(job_name)
    openshift = Openshift(logger=logger)

    try:
        openshift.login("test-admin", "test")
        max_retry = 10
        retry = 0
        # waiting for delivery get completed before next job for the same
        # project overrides the job parameters
        while openshift.get_project(project_name_hash) and (retry < max_retry):
            time.sleep(50)
            retry += 1

        if openshift.get_project(project_name_hash):
            logger.error("OpenShift is not able to delete project: {}"
                         .format(job_name))
            raise
        else:
            openshift.create(project_name_hash)
    except OpenshiftError:
        try:
            openshift.delete(project_name_hash)
        except OpenshiftError as e:
            logger.error(e)
        return

    try:
        template_path = os.path.join(
            os.path.dirname(__file__), 'template.json')
        openshift.upload_template(project_name_hash, template_path, {
            'SOURCE_REPOSITORY_URL': job.get("repo_url"),
            'REPO_BRANCH': job.get("repo_branch"),
            'APPID': job.get("appid"),
            'JOBID': job.get("jobid"),
            'REPO_BUILD_PATH': job.get("repo_build_path"),
            'TARGET_FILE': job.get("target_file"),
            'NOTIFY_EMAIL': job.get("notify_email"),
            'DESIRED_TAG': job.get("desired_tag"),
            'TEST_TAG': job.get("test_tag")
        })
    except OpenshiftError:
        try:
            openshift.delete(project_name_hash)
        except OpenshiftError as e:
            logger.error(e)
        return

    job["action"] = "start_build"

    build = Build.objects.get(uuid=job['uuid'])
    build_phase = BuildPhase.objects.get_or_create(build=build, phase='build')

    queue.put(json.dumps(job), 'master_tube')
    build_phase.status = 'queued'
    build_phase.save()
