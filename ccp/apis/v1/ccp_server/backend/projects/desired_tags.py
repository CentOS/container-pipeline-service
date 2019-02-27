# Process response for api/v1/$namespace/$app_id/$job_id/desired-tags
from ccp.apis.v1.ccp_server import meta_obj

from ccp.apis.v1.ccp_server.models.app_id_job_id_tags import\
    AppIdJobIdTags
from ccp.apis.v1.ccp_server.models.app_id_job_id_tag import\
    AppIdJobIdTag
from ccp.index_reader import Project, IndexReader
from os import path
from shutil import rmtree
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.apis.v1.ccp_server.backend.index_update_checker import \
    check_index_seed_job_update
from ccp.apis.v1.ccp_server.env_config import *


def response(namespace, app_id, job_id):
    """
    """
    ojbi = OpenshiftJenkinsBuildInfo(
        JENKINS_URL,
        token_from_mount=SERVICE_ACCOUNT_SECRET_MOUNT_PATH,
        namespace=namespace
    )

    check_index_seed_job_update(namespace=namespace)
    index_location = path.join(INDEX_CLONE_LOCATION, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()
    tags = []
    for p in prjs:
        if p.app_id == app_id and p.job_id == job_id:
            tags.append(p.desired_tag)

    ajtds = []
    if len(tags) == 0:
        return {}

    for tag in tags:
        jenkins_job_name = "{}-{}".format(
            namespace,
            Project.pipeline_name(
                app_id=app_id, job_id=job_id, desired_tag=tag
            )
        )
        build_status = ojbi.get_build_status(
            ordered_job_list=[
                namespace,
                jenkins_job_name
            ],
            build_number="lastBuild"
        )
        image = "{}/{}".format(app_id, job_id)
        ajtd = AppIdJobIdTag(image=image, desired_tag=tag,
                             build_status=build_status)
        ajtds.append(ajtd)

    return AppIdJobIdTags(
        meta=meta_obj(), app_id=app_id,
        job_id=job_id, tags=ajtds
    )

