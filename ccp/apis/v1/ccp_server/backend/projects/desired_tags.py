# Process response for api/v1/$namespace/$app_id/$job_id/desired-tags
from ccp.apis.v1.ccp_server import meta_obj

from ccp.apis.v1.ccp_server.models.app_id_job_id_tags import\
    AppIdJobIdTags
from ccp.apis.v1.ccp_server.models.app_id_job_id_tag import\
    AppIdJobIdTag
from ccp.index_reader import Project, IndexReader
from ccp.lib.clients.git.client import GitClient
from os import path
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.apis.v1.ccp_server.env_config import *


def response(namespace, app_id, job_id):
    """
    """
    ojbi = OpenshiftJenkinsBuildInfo(
        JENKINS_URL,
        token_from_mount=SERVICE_ACCOUNT_SECRET_MOUNT_PATH,
        namespace=namespace
    )

    gc = GitClient(
        git_url=INDEX_GIT_URL,
        git_branch=INDEX_GIT_BRANCH
    )
    gc.fresh_clone()
    index_location = path.join(gc.actual_clone_location, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()
    tags = []
    for p in prjs:
        if p.app_id == appid and p.job_id == jobid:
            tags.append(p.desired_tag)

    ajtds = []
    if len(tags) == 0:
        return {}

    for tag in tags:
        jenkins_job_name = "{}-{}".format(
            namespace,
            Project.pipeline_name(
                app_id=appid, job_id=jobid, desired_tag=tag
            )
        )
        build_status = ojbi.get_build_status(
            ordered_job_list=[
                namespace,
                jenkins_job_name
            ],
            build_number="lastBuild"
        )
        image = "{}/{}".format(appid, jobid)
        ajtd = AppIdJobIdTag(image=image, desired_tag=tag,
                             build_status=build_status)
        ajtds.append(ajtd)

    return AppIdJobIdTags(
        meta=meta_obj(), app_id=appid,
        job_id=jobid, tags=ajtds
    )

