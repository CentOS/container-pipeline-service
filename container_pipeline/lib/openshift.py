import logging
import subprocess
import time

from container_pipeline.lib import settings
from container_pipeline.lib.command import run_cmd


class OpenshiftError(Exception):
    pass


class Openshift(object):

    def __init__(self, endpoint=None, user=None, password=None,
                 config=None, cert=None, logger=None):
        self.endpoint = endpoint or settings.OPENSHIFT_ENDPOINT
        self.user = user or settings.OPENSHIFT_USER
        self.password = password or settings.OPENSHIFT_PASSWORD
        self.config = config or settings.OC_CONFIG
        self.cert = cert or settings.OC_CERT
        self.oc_cmd_suffix = (
            '--config {config} --certificate-authority {cert}'.format(
                config=self.config, cert=self.cert))
        self.logger = logger or logging.getLogger('console')

    def login(self, user=None, password=None):
        """Login to openshift"""
        user = user or self.user
        password = password or self.password
        try:
            self.logger.debug(
                'Login to openshift:\n{}'.format(
                    run_cmd(
                        'oc login {endpoint} -u {user} -p {password} {suffix}'
                        .format(
                            endpoint=self.endpoint, user=user,
                            password=password, suffix=self.oc_cmd_suffix
                        ))
                )
            )
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Openshift login error: {}'.format(e))

    def use_project(self, project):
        """Use an openshift project"""
        self.logger.debug('Using openshift project: {}'.format(project))
        try:
            self.logger.debug(
                'oc project {project} {suffix}'.format(
                    project=project, suffix=self.oc_cmd_suffix))
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Unable to use openshift project {}: {}'.format(project, e))

    def build(self, project, build):
        """Run build for a project"""
        self.logger.debug('Run openshift project build: {}/{}'
                          .format(build, project))
        try:
            output = run_cmd(
                'oc --namespace {project} start-build {build} '
                '{suffix}'.format(
                    project=project, build=build, suffix=self.oc_cmd_suffix)
            )
            self.logger.debug('Openshift project build run output: {}/{}\n{}'
                              .format(project, build, output))
            build_id = output.split('"')[-1].rstrip()
            return build_id
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Unable to run build project build: {}/{}\nError: {}'
                .format(project, build, e))

    def get_build_status(self, project, build_id):
        """Get status of an openshift project build"""
        try:
            output = run_cmd(
                'oc get --namespace {project} build/{build_id} {suffix} | '
                'grep -v STATUS'.format(
                    project=project, build_id=build_id,
                    suffix=self.oc_cmd_suffix),
                shell=True
            )
            self.logger.debug('Openshift build status for: {}/{}\n{}'
                              .format(project, build_id, output))
            return output.split()[3]
        except subprocess.CalledProcessError as e:
            self.logger.error(
                'Openshift build status fetch error for {}/{}: {}'
                .format(project, build_id, e))
            return ""

    def wait_for_build_status(self, project, build_id, status,
                              empty_retries=10, retry_delay=30):
        """Wait for openshift project build to reach a desired state"""
        self.logger.debug('Wait for openshift project build: {}/{} to '
                          'be: {}'.format(project, build_id, status))
        current_status = None
        empty_retry_count = 0
        while True:
            current_status = self.get_build_status(project, build_id)
            if current_status == status:
                return True
            elif not current_status:
                self.logger.debug('Failed to fetch build status for: {}/{}'
                                  .format(project, build_id))
                if empty_retry_count == empty_retries:
                    self.logger.debug(
                        'Exceeded max retries for checking build status for: '
                        '{}/{}. Assuming failure.'.format(project, build_id))
                    return False
                empty_retry_count += 1
                self.logger.debug('Retrying {}/{} to check build status for : '
                                  '{}/{}'.format(project, build_id))
            elif current_status.lower() == 'failed':
                    return False
            else:
                empty_retry_count = 0
            time.sleep(retry_delay)

    def get_build_logs(self, project, build_id):
        try:
            output = run_cmd(
                'oc logs --namespace {project} build/{build_id} {suffix}'
                .format(
                    project=project, build_id=build_id,
                    suffix=self.oc_cmd_suffix))
            self.logger.debug('Build logs for project build: {}/{}\n{}'.format(
                project, build_id, output))
        except subprocess.CalledProcessError as e:
            self.logger.error(
                'Could not retrieve build logs for project build: '
                '{}/{}\n{}'.format(project, build_id, e))
            output = 'Could not retrieve build logs'
        return output
