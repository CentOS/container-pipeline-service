import logging
import os
import sys
import time

from container_pipeline.lib.log import load_logger
from trigger_dockerfile_lint import trigger_dockerfile_linter

if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('jenkins')
    (appid, jobid, repo_url, repo_branch, repo_build_path,
     target_file, notify_email, desired_tag, depends_on,
     test_tag) = sys.argv[1:]
    try:
        trigger_dockerfile_linter(
            appid, jobid, repo_url, repo_branch,
            repo_build_path, target_file, notify_email,
            desired_tag, depends_on, test_tag)
    except:
        sys.exit(1)
