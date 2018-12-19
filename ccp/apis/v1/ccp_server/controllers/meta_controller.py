import connexion
import six

from ccp.apis.v1.ccp_server.models.namespaces import\
    Namespaces # noqa: E501
from ccp.apis.v1.ccp_server.backend.meta.namespaces import response as \
    ns_response
from ccp.apis.v1.ccp_server.backend.meta.projects import response as \
    projects_response
from ccp.apis.v1.ccp_server.models.projects import Projects  # noqa: E501
from ccp.apis.v1.ccp_server import util


def namespace_projects(namespace):  # noqa: E501
    """Get all the projects in given namespace

     # noqa: E501

    :param namespace: namespace to list projects from
    :type namespace: str

    :rtype: Projects
    """
    return projects_response(namespace=namespace)


def namespaces():  # noqa: E501
    """Get all available namespaces accessible over APIs

     # noqa: E501


    :rtype: Namespaces
    """
    return ns_response()
