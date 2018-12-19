# Process response for /$namespace/$app_id/$job_id/$desired-tag/builds
from ccp.apis.v1.ccp_server import meta_obj
from ccp.apis.v1.ccp_server.models.project_build_name_status import\
    ProjectBuildNameStatus
from ccp.apis.v1.ccp_server.models.project_builds_info import ProjectBuildsInfo
from ccp.apis.v1.ccp_server.models.project_builds import ProjectBuilds
from ccp.index_reader import Project
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.apis.v1.ccp_server.env_config import *

from typing import List, Dict  # noqa: F401


def response(namespace, appid, jobid, desired_tag):
    """
    """
    ojbi = OpenshiftJenkinsBuildInfo(
        JENKINS_URL,
        token_from_mount=SERVICE_ACCOUNT_SECRET_MOUNT_PATH,
        namespace=namespace
    )
    job_name = Project.pipeline_name(
        app_id=appid, job_id=jobid, desired_tag=desired_tag
    )
    jenkins_job_name = "{}-{}".format(
        namespace,
        job_name
    )
    bns = ojbi.get_build_numbers(
        ordered_job_list=[
            namespace,
            jenkins_job_name
        ]
    )
    pbi = List[ProjectBuilds]
    for k, v in bns:
        t = ProjectBuildNameStatus(str(k), str(v))
        t1 = ProjectBuilds(build_number=t)
        pbi += t1
    return ProjectBuildsInfo(
        builds=pbi, meta=meta_obj()
    )
