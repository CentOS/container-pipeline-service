import connexion
import six

from ccp.apis.server.ccp_server.models.namespaces import\
    Namespaces # noqa: E501
from ccp.apis.server.ccp_server.models.projects import Projects  # noqa: E501
from ccp.apis.server.ccp_server import util


def namespace_projects(namespace):  # noqa: E501
    """Get all the projects in given namespace

     # noqa: E501

    :param namespace: namespace to list projects from
    :type namespace: str

    :rtype: Projects
    """
    return 'do some magic!'


def namespaces():  # noqa: E501
    """Get all available namespaces accessible over APIs

     # noqa: E501


    :rtype: Namespaces
    """
    return 'do some magic!'
