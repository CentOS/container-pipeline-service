# Process response for api/v1/projects

from ccp.apis.v1.ccp_server.models.projects import Projects
from ccp.apis.v1.ccp_server.models.project import Project
from ccp.lib.clients.openshift.client import OpenShiftCmdClient
from ccp.apis.v1.ccp_server.env_config import *
from ccp.apis.v1.ccp_server import meta_obj
from ccp.index_reader import IndexReader
from ccp.lib.clients.git.client import GitClient
from os import path
from shutil import rmtree


def response(namespace):
    """
    """
    ocl = OpenShiftCmdClient()
    """
    ocl.login(
        server=OPENSHIFT_URL,
        token=ocl.get_token_from_mounted_secret(
            secret_mount_path=SERVICE_ACCOUNT_SECRET_MOUNT_PATH
        )
    )
    """
    gc = GitClient(
        git_url=INDEX_GIT_URL,
        git_branch=INDEX_GIT_BRANCH
    )
    gc.fresh_clone()
    index_location = path.join(gc.actual_clone_location, "index.d")
    ir = IndexReader(index_location, namespace)
    projects = []
    prjs = ir.read_projects()
    for p in prjs:
        projects.append(
            Project(
                app_id=p.app_id,
                job_id=p.job_id,
                desired_tag=p.desired_tag
            )
        )
    projects_in_namespace = Projects(
        meta=meta_obj(),
        projects=projects
    )

    try:
        rmtree(gc.actual_clone_location)
    except OSError as e:
        print ("Error: {} - {}".format(e.filename, e.strerror))

    return projects_in_namespace
