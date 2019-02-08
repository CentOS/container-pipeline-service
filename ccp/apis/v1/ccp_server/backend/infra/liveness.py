"""
Process response for api/v1/liveness
"""
from ccp.apis.v1.ccp_server.models.status import Status
from ccp.apis.v1.ccp_server import meta_obj


def response():
    """
    Return the response for /api/v1/liveness
    """
    # TODO: Grab the actual status here
    return Status(meta=meta_obj(), status="OK")
