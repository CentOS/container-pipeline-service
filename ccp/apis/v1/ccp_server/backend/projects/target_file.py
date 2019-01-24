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
    gc.fresh_clone()
    index_location = path.join(gc.actual_clone_location, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()

    target_file = ""
    source_repo = ""
    source_branch = ""
    pre_build = False

    for p in prjs:
        if p.app_id == app_id and p.job_id == job_id and \
                p.desired_tag == desired_tag:
            source_repo = p.git_url
            source_branch = p.git_branch
            target_file = "{}/{}".format(p.git_path, p.target_file)
            pre_build = p.pre_build_script and p.pre_build_context
            break

    try:
        rmtree(gc.actual_clone_location)
    except OSError as e:
        print ("Error: {} - {}".format(e.filename, e.strerror))

    if source_repo == "":
        return {}

    target_file_link = "{}/{}/{}".format(
        source_repo, source_branch, target_file
    )

    if "github.com" in target_file_link:
        target_file_link = target_file_link.replace(
            "github.com","raw.githubusercontent.com")

    source_repo_with_branch = "{}/tree/{}".format(source_repo, source_branch)

    return TargetFile(
        meta=meta_obj(), prebuild=pre_build,
        target_file_link=target_file_link, source_repo=source_repo_with_branch
    )
