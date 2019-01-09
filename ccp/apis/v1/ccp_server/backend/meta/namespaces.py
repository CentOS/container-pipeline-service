# Process response for api/v1/namespaces
from ccp.lib.clients.openshift.client import OpenShiftCmdClient
from ccp.lib.processors.pipeline_information.openshift import \
    OpenShiftCommandProcessor
from ccp.apis.v1.ccp_server.models.namespaces import Namespaces
from ccp.apis.v1.ccp_server import meta_obj
from ccp.apis.v1.ccp_server.env_config import *


def response():
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
    ocp = OpenShiftCommandProcessor()
    return Namespaces(
        meta=meta_obj("v1"),
        namespaces=ocp.get_namespaces()
    )
