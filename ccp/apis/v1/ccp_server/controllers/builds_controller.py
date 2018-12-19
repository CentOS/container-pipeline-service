import connexion
import six

from ccp.apis.v1.ccp_server.models.build_logs import BuildLogs  # noqa: E501
from ccp.apis.v1.ccp_server.models.project_builds_info import\
    ProjectBuildsInfo  # noqa: E501
from ccp.apis.v1.ccp_server.models.weekly_scan_builds_info import\
    WeeklyScanBuildsInfo  # noqa: E501
from ccp.apis.v1.ccp_server.models.weekly_scan_logs import\
    WeeklyScanLogs  # noqa: E501
from ccp.apis.v1.ccp_server import util
from ccp.apis.v1.ccp_server.backend.builds.builds import \
    response as builds_response
from ccp.apis.v1.ccp_server.backend.builds.build_logs import response as\
    build_logs_response


def project_build_logs(namespace, app_id, job_id, desired_tag, build):  # noqa: E501
    """Build logs for given build number

    Build logs for given build number of the project # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str
    :param desired_tag: desired-tag of the project
    :type desired_tag: str
    :param build: build number
    :type build: str

    :rtype: BuildLogs
    """
    return build_logs_response(
        namespace=namespace,
        appid=app_id,
        jobid=job_id,
        desired_tag=desired_tag,
        build=build
    )


def project_builds(namespace, app_id, job_id, desired_tag):  # noqa: E501
    """Get all the builds info for given project

    Get all the builds number, name and status for given project # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str
    :param desired_tag: desired-tag of the project
    :type desired_tag: str

    :rtype: ProjectBuildsInfo
    """
    return builds_response(
        namespace=namespace,
        appid=app_id,
        jobid=job_id,
        desired_tag=desired_tag
    )


def project_wscan_build_logs(namespace, app_id, job_id, desired_tag, build):  # noqa: E501
    """Weekly scan logs for given wscan-build number

    Weekly scan logs for given wscan-build number of the # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str
    :param desired_tag: desired-tag of the project
    :type desired_tag: str
    :param build: build number
    :type build: str

    :rtype: WeeklyScanLogs
    """
    return 'do some magic!'


def project_wscan_builds(namespace, app_id, job_id, desired_tag):  # noqa: E501
    """Get all the weekly scan builds information for given project

    Get all the weekly scan builds information for given project # noqa: E501

    :param namespace: namespace of the project
    :type namespace: str
    :param app_id: app-id of the project
    :type app_id: str
    :param job_id: job-id of the project
    :type job_id: str
    :param desired_tag: desired-tag of the project
    :type desired_tag: str

    :rtype: WeeklyScanBuildsInfo
    """
    return 'do some magic!'
