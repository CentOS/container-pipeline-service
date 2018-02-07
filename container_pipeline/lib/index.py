import os
from glob import glob
from container_pipeline.utils import load_yaml

import container_pipeline.constants.index
import logging
import yaml


class IndexEntry(object):

    def __init__(self, data):
        self._initialize_data(
            data.get(container_pipeline.constants.index.ID),
            data.get(container_pipeline.constants.index.APP_ID),
            data.get(container_pipeline.constants.index.JOB_ID),
            str(data.get(container_pipeline.constants.index.DESIRED_TAG)),
            data.get(container_pipeline.constants.index.GIT_URL),
            data.get(container_pipeline.constants.index.GIT_PATH),
            data.get(container_pipeline.constants.index.GIT_BRANCH),
            data.get(container_pipeline.constants.index.TARGET_FILE),
            data.get(container_pipeline.constants.index.NOTIFY_EMAIL),
            data.get(container_pipeline.constants.index.BUILD_CONTEXT),
            data.get(container_pipeline.constants.index.PREBUILD_SCRIPT),
            data.get(container_pipeline.constants.index.PREBUILD_CONTEXT),
            data.get(container_pipeline.constants.index.DEPENDS_ON)
        )

    def _initialize_data(self, id, app_id, job_id, desired_tag, git_url,
                         git_path, git_branch, target_file, notify_email,
                         build_context, prebuild_script, prebuild_context,
                         depends_on):
        self.id = id
        self.app_id = app_id
        self.job_id = job_id
        self.desired_tag = desired_tag
        self.git_url = git_url
        self.git_path = git_path
        self.git_branch = git_branch
        self.target_file = target_file
        self.notify_email = notify_email
        self.build_context = build_context
        self.prebuild_script = prebuild_script
        self.prebuild_context = prebuild_context
        self.depends_on = depends_on


def get_entries(index_path, exception_on_fail=False, logger=None):
    logger = logger or logging.getLogger('console')
    entries = []
    if not os.path.exists(index_path):
        msg = str.format(
            "Invalid index path specified {}",
            index_path
        )
        logger.debug(msg)
        if exception_on_fail:
            raise Exception(msg)
    index_d_path = os.path.join(index_path, "index.d")
    if not os.path.exists(index_d_path):
        msg = str.format(
            "Index path does not container index.d {}",
            index_path
        )
        logger.debug(msg)
        if exception_on_fail:
            raise Exception(msg)
    potential_files = glob(
        str.format("{}/*.y*ml", index_d_path)
    )

    for potential_file in potential_files:
        if container_pipeline.constants.index.INDEX_TEMPLATE not in \
                potential_file:
            data = load_yaml(potential_file)
            if data:
                if "Projects" in data:
                    for entry in data["Projects"]:
                        entries.append(
                            IndexEntry(entry)
                        )
    return entries
