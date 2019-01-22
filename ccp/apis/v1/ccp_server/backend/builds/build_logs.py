# Process response for /$namespace/$app_id/$job_id/$desired-tag/$build/build-logs
from ccp.apis.v1.ccp_server import meta_obj
from ccp.lib.processors.pipeline_information.builds import \
    OpenshiftJenkinsBuildInfo
from ccp.apis.v1.ccp_server.models.build_logs import BuildLogs
from ccp.apis.v1.ccp_server.models.prebuild_lint_build_scan_logs import \
    PrebuildLintBuildScanLogs
from ccp.apis.v1.ccp_server.models.scanner_logs import ScannerLogs
from ccp.apis.v1.ccp_server.models.all_scanner_logs import AllScannerLogs
from ccp.index_reader import Project, IndexReader
from ccp.lib.clients.git.client import GitClient
from os import path
from ccp.apis.v1.ccp_server.env_config import *

from typing import List, Dict  # noqa: F401


def process_log(log_obj, stage):
    logs = None
    if log_obj and len(log_obj.keys()) > 0:
        for k, v in log_obj:
            if k == stage:
                logs = "{}<br />\n{}".format(
                    k,
                    v
                )
                break
    return logs


def response(namespace, appid, jobid, desired_tag, build):
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
    logs_info =ojbi.get_build_logs(
        ordered_job_list=[
            namespace,
            jenkins_job_name
        ],
        build_number=build
    )

    gc = GitClient(
        git_url=INDEX_GIT_URL,
        git_branch=INDEX_GIT_BRANCH
    )
    gc.fresh_clone()
    index_location = path.join(gc.clone_location, "index.d")
    ir = IndexReader(index_location, namespace)
    prjs = ir.read_projects()
    prebuild_exists = False
    for p in prjs:
        if p.app_id == appid and p.job_id == jobid and \
                p.desired_tag == desired_tag:
            prebuild_exists = p.pre_build_context and p.pre_build_script
            break
    prebuild_logs = process_log(logs_info, "Prebuild source repo") if \
        prebuild_exists else "Prebuild not requested"
    lint_logs = process_log(logs_info, "Lint the Dockerfile")
    build_logs = process_log(logs_info, "Build the container image")

    # TODO : Update this once logs are seperated as scans
    scan_logs = process_log(logs_info, "Scan the image")
    extracted_scan_logs = ScannerLogs(
        logs=scan_logs, description="All Scanners logs"
    )
    all_scan_logs = AllScannerLogs(
        scanner_name=[extracted_scan_logs]
    )
    logs = PrebuildLintBuildScanLogs(
        prebuild=str(prebuild_logs),
        lint=str(lint_logs),
        build=str(build_logs),
        scan=all_scan_logs
    )
    return BuildLogs(
        meta=meta_obj(),
        pre_build=prebuild_exists,
        status=(lint_logs and build_logs and scan_logs),
        failed_stage="TODO",
        logs=logs
    )
