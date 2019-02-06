# Process response for /$namespace/$app_id/$job_id/$desired-tag/target_file
from ccp.apis.v1.ccp_server import meta_obj
from ccp.apis.v1.ccp_server.models.target_file import TargetFile

from ccp.index_reader import Project,IndexReader
from ccp.lib.clients.git.client import GitClient
from os import path
from shutil import rmtree

from ccp.apis.v1.ccp_server.env_config import *

def response(namespace, app_id, job_id, desired_tag):
    """
    """
    gc = GitClient(
        git_url=INDEX_GIT_URL,
        git_branch=INDEX_GIT_BRANCH
    )

    index_location = path.join(gc.actual_clone_location, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()

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
        source_branch = source_branch
    )
