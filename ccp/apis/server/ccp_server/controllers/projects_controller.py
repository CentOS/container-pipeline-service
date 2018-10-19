import connexion
import six

from ccp.apis.server.ccp_server.models.app_id_job_id_tags import\
    AppIdJobIdTags  # noqa: E501
from ccp.apis.server.ccp_server.models.project_metadata import\
    ProjectMetadata  # noqa: E501
from ccp.apis.server.ccp_server.models.target_file import\
    TargetFile  # noqa: E501
from ccp.apis.server.ccp_server import util


def project_desired_tags(namespace, app_id, job_id):  # noqa: E501
    """Get tags for given $app_id/$job_id with build status and image

    Get all the tags defined for given $app_id/$job_id along with latest build status and image name # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str

    :rtype: AppIdJobIdTags
    """
    return 'do some magic!'


def project_metadata(namespace, app_id, job_id, desired_tag):  # noqa: E501
    """Get the metadata of the given project

    Get the metadata of project as provided in container index # noqa: E501

    :param namespace: namespace to list projects from
    :type namespace: str
    :param app_id: app-id
    :type app_id: str
    :param job_id: job-id
    :type job_id: str
    :param desired_tag: desired-tag
    :type desired_tag: str

    :rtype: ProjectMetadata
    """
    return 'do some magic!'


def project_target_file(namespace, app_id, job_id, desired_tag):  # noqa: E501
    """Get Dockerfile for given project

    Get Dockerfile for given project # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str
    :param desired_tag: desired-tag of the project
    :type desired_tag: str

    :rtype: TargetFile
    """
    return 'do some magic!'
