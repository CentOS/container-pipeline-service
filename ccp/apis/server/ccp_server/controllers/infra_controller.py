"""
Controller for /api/v1/liveness
"""

from ccp.apis.server.ccp_server.models.status import Status  # noqa: E501
from ccp.apis.server.ccp_server.backend.v1.infra.liveness import response


def liveness():  # noqa: E501
    """Get the liveness of API service

     # noqa: E501


    :rtype: Status
    """
    return response()
