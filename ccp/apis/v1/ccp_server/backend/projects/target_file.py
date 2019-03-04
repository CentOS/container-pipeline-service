# Process response for /$namespace/$app_id/$job_id/$desired-tag/target_file
from ccp.apis.v1.ccp_server import meta_obj
from ccp.apis.v1.ccp_server.models.target_file import TargetFile

from ccp.index_reader import Project,IndexReader
from os import path
from shutil import rmtree

from ccp.apis.v1.ccp_server.backend.index_update_checker import \
    check_index_seed_job_update
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.apis.v1.ccp_server.env_config import *

def response(namespace, app_id, job_id, desired_tag):
    """
    """
    check_index_seed_job_update(namespace=namespace)
    index_location = path.join(INDEX_CLONE_LOCATION, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()
    job_name =  Project.pipeline_name(
        app_id=appid, job_id=jobid, desired_tag=desired_tag
    )

    latest_build_number = ojbi.get_latest_build_number(
        ordered_job_list=[
            namespace,
            "{}-{}".format(
                namespace,
                job_name
            )
        ]
    )

    if not latest_build_number:
        latest_build_number="0"

    target_file_path = ""
    source_repo = ""
    source_branch = ""
    pre_build_exists = False

    for p in prjs:
        if p.app_id == app_id and p.job_id == job_id and \
                p.desired_tag == desired_tag:
            source_repo = p.git_url
            source_branch = p.git_branch
            target_file_path = "{}/{}".format(p.git_path, p.target_file)
            pre_build_exists = p.pre_build_script and p.pre_build_context
            break

    if source_repo == "":
        return {}

    if source_repo.endswith(".git"):
        source_repo = source_repo[:-4]

    if not pre_build_exists:
        pre_build_exists=False

    return TargetFile(
        meta=meta_obj(), prebuild=pre_build_exists,
        target_file_path=target_file_path, source_repo=source_repo,
        source_branch = source_branch, latest_build_number=latest_build_number
    )
