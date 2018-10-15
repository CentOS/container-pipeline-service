import connexion
import six

from ccp_server.models.status import Status  # noqa: E501
from ccp_server import util


def liveness():  # noqa: E501
    """Get the liveness of API service

     # noqa: E501


    :rtype: Status
    """
    return 'do some magic!'
