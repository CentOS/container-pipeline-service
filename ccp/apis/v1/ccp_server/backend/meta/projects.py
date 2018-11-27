# Process response for api/v1/projects

from ccp.apis.v1.ccp_server.models.projects import Projects
from ccp.apis.v1.ccp_server.models.project import Project
from ccp.lib.clients.openshift.client import OpenShiftCmdClient
from ccp.apis.v1.ccp_server.env_config import *
from ccp.apis.v1.ccp_server import meta_obj


def response(namespace):
    """
    """
    ocl = OpenShiftCmdClient()
    ocl.login(
        server=OPENSHIFT_URL,
        token=ocl.get_token_from_mounted_secret(
            secret_mount_path=SERVICE_ACCOUNT_SECRET_MOUNT_PATH
        )
    )
    projects_ = []
    projects_in_namespace = Projects(
        meta=meta_obj(),
        projects=projects_
    )
    return projects_in_namespace
