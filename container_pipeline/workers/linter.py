#!/usr/bin/env python

import json
import logging
import os

from container_pipeline.lib import dj  # noqa
from django.utils import timezone

from container_pipeline.lib import settings
from container_pipeline.lib.command import run_cmd_out_err
from container_pipeline.lib.log import load_logger
from container_pipeline.trigger_build import create_project
from container_pipeline.utils import get_project_name
from container_pipeline.workers.base import BaseWorker
from container_pipeline.models import Build, BuildPhase


class DockerfileLintWorker(BaseWorker):
    """
    Dockerfile lint worker lints the Dockerfile using the projectatomic's
    dockerfile_lint tool. https://github.com/projectatomic/dockerfile_lint
    """
    NAME = 'Linter worker'

    def __init__(self, logger=None, sub=None, pub=None):
        super(DockerfileLintWorker, self).__init__(logger, sub, pub)
        self.build_phase_name = 'dockerlint'
        self.status_file_path = ""
        self.project_name = None

    def handle_job(self, job):
        """
        This menthod handles the job received for dockerfile lint worker.
        """
        # linter execution status file path
        self.status_file_path = os.path.join(
            job.get("logs_dir"),
            settings.LINTER_STATUS_FILE
        )
        self.job = job
        self.setup_data()
        self.set_buildphase_data(
            build_phase_status='processing',
            build_phase_start_time=timezone.now()
        )

        self.logger.info("Received job for Dockerfile lint: %s" % job)
        self.logger.debug("Writing Dockerfile to /tmp/scan/Dockerfile")
        self.write_dockerfile(job.get("dockerfile"))
        self.logger.debug("Running Dockerfile Lint check")
        self.lint()

    def write_dockerfile(self, dockerfile):
        """
        Write dockerfile at temporary location to run lint upon
        """
        if os.path.isdir("/tmp/scan"):
            self.logger.debug("/tmp/scan directory already exists")
        elif os.path.isfile("/tmp/scan"):
            os.remove("/tmp/scan")
            os.makedirs("/tmp/scan")
        else:
            os.makedirs("/tmp/scan")

        with open("/tmp/scan/Dockerfile", "w") as f:
            f.write(dockerfile)

    def lint(self):
        """
        Lint the Dockerfile received
        """
        command = ("docker",
                   "run",
                   "--rm",
                   "-v",
                   "/tmp/scan:/root/scan:Z",
                   "registry.centos.org/pipeline-images/dockerfile-lint")

        try:
            out, err = run_cmd_out_err(command)
            if err == "":
                response = self.handle_lint_success(out)
            else:
                response = self.handle_lint_failure(err)
                self.job["dockerfile"] = None
                self.job["action"] = "notify_user"
                self.queue.put(json.dumps(self.job), 'master_tube')
        except Exception as e:
            self.logger.warning(
                "Dockerfile Lint check command failed", extra={'locals':
                                                                   locals()})
            response = self.handle_lint_failure(str(e))

            self.job["dockerfile"] = None
            self.job["action"] = "notify_user"
            self.queue.put(json.dumps(self.job), 'master_tube')
            self.set_buildphase_data(
                build_phase_status='error',
                build_phase_end_time=timezone.now()
            )
        finally:
            # remove the Dockerfile to have a clean environment on next run
            self.logger.info("Removing Dockerfile from /tmp/scan/Dockerfile")
            os.remove("/tmp/scan/Dockerfile")

            # now export the status about linter execution in logs dir of the
            # job this response will be read after job builds and while sending
            # email to user. Details from this response is used to generate
            # email.

            # TODO: Write export JSON method in base worker
            self.export_linter_status(response, self.status_file_path)

    def handle_lint_success(self, output):
        self.logger.info("Dockerfile Lint check done. Exporting logs.")
        # logs file for linter
        linter_results_path = os.path.join(
            self.job.get("logs_dir"),
            settings.LINTER_RESULT_FILE
        )

        # logs URL for linter results
        logs_URL = linter_results_path.replace(
            settings.LOGS_DIR_BASE,   # /srv/pipeline-logs/
            settings.LOGS_URL_BASE   # https://registry.centos.org
        )

        output += "\nHosted linter results : %s\n" % logs_URL
        # export linter results
        self.export_logs(output, linter_results_path)

        response = {
            "logs": output,
            "lint_status": True,
            "namespace": self.job.get('appid'),
            "notify_email": self.job.get("notify_email"),
            "job_name": self.job.get("job_name"),
            "msg": None,
            "linter_results_path": linter_results_path,
            "logs_URL": logs_URL,
        }
        self.set_buildphase_data(
            build_phase_status='complete',
            build_phase_end_time=timezone.now()
        )

        # remove Dockerfile from the job data as it's not needed anymore
        if "dockerfile" in self.job:
            self.logger.info("Deleting 'dockerfile' data from job")
            self.job["dockerfile"] = None

        create_project(self.queue, self.job, self.logger)
        return response

    def handle_lint_failure(self, error):
        self.logger.warning("Dockerfile Lint check failed")
        self.logger.error(error)

        response = {
            "lint_status": False,
            "namespace": self.job.get('appid'),
            "notify_email": self.job.get("notify_email"),
            "job_name": self.job.get("job_name"),
            "msg": error,
            "project_name": self.project_name
        }
        self.set_buildphase_data(
            build_phase_status='failed',
            build_phase_end_time=timezone.now()
        )

        return response

    def export_linter_status(self, status, status_file_path):
        """
        Export status of linter execution for build in process
        """
        try:
            with open(self.status_file_path, "w") as fin:
                json.dump(status, fin)
        except IOError as e:
            self.logger.error(
                "Failed to write linter status on NFS share: {}".format(e))
        else:
            self.logger.debug(
                "Wrote linter status to file: %s" % self.status_file_path)


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('dockerfile-linter')
    worker = DockerfileLintWorker(
        logger, sub='start_linter', pub='master_tube')
    worker.run()