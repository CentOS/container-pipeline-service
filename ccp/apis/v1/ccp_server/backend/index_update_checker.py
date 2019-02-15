# -*- coding: utf-8 -*-
"""
This file contains utils that checks if the cloned index is updated one
"""
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.lib.clients.git.client import GitClient

from ccp.apis.v1.ccp_server.env_config import *
from pathlib import Path

def get_latest_index():
    gc = GitClient(
        git_url=INDEX_GIT_URL,
        git_branch=INDEX_GIT_BRANCH,
        clone_location=INDEX_CLONE_LOCATION
    )
    gc.pull_remote()
    return "index updated"

def check_index_seed_job_update(namespace):
    ojbi = OpenshiftJenkinsBuildInfo(
        JENKINS_URL,
        token_from_mount=SERVICE_ACCOUNT_SECRET_MOUNT_PATH,
        namespace=namespace
    )
    job_name = "{}-{}".format(
        namespace,
        "seed-job"
    )
    last_build_details = ojbi.get_build_status(
        ordered_job_list=[namespace,job_name],
        build_number="lastBuild"
    )
    last_build_number = last_build_details["number"]
    seed_job_build_info_path = "/var/index/seed_job_build_number"
    last_processed_build_number = ""
    try:
        seed_job_build_info = Path(seed_job_build_info_path)
        if seed_job_build_info.is_file():
            last_processed_build_number = open(seed_job_build_info_path, "r")
            if str(last_build_number) == str(last_processed_build_number):
                return "already updated"
            else:
                return get_latest_index()
        else:
            return get_latest_index()
    except:
        return "could not update index"

