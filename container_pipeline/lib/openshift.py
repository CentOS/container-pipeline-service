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

    def get_project(self, project):
        self.logger.debug(
            'Check openshift project: {} existing or not'.format(project))
        is_existing = False
        try:
            output = run_cmd(
                'oc get projects {suffix}'.format(suffix=self.oc_cmd_suffix))
            if project in output.strip():
                is_existing = True
        except subprocess.CalledProcessError as e:
            self.logger.debug('Error during fetching details for \
                              openshift project  {}: {}'.format(project, e))
        return is_existing

    def create(self, project):
        self.logger.debug('Create openshift project: {}'.format(project))
        try:
            run_cmd(
                'oc new-project {project} --display-name {project} {suffix}'
                .format(project=project, suffix=self.oc_cmd_suffix))
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Error during creating openshift project {}: {}'.format(
                    project, e))

    def delete(self, project):
        self.logger.debug('Delete openshift project: {}'.format(project))
        try:
            run_cmd(
                'oc delete project {project} {suffix}'
                .format(project=project, suffix=self.oc_cmd_suffix))
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Error during deleting openshift project {}: {}'.format(
                    project, e))

    def clean_project(self, project):
        try:
            run_cmd(
                'oc delete build,bc,is -n {project} {suffix}'
                .format(project=project, suffix=self.oc_cmd_suffix))
        except subprocess.CalledProcessError as e:
            self.logger.error('Error during cleaning project {}: {}'.format(
                project, e))

    def upload_template(self, project, template_path, template_data):
        """Upload processed template for project from template path"""
        self.logger.debug('Uploading template data: {} for project: {} from '
                          'template: {}'.format(
                              template_data, project, template_path))
        tmpl_params_str = ' '.join(
            ['-v {k}={v}'.format(k=k, v=v) for k, v in template_data.items()])
        try:
            run_cmd(
                'oc process -n {project} -f {tmpl_path} {tmpl_params} '
                '{suffix} | '
                'oc {suffix} -n {project} create -f -'.format(
                    project=project, tmpl_path=template_path,
                    tmpl_params=tmpl_params_str, suffix=self.oc_cmd_suffix),
                shell=True)
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Error during uploading processed template for project {}: {}'
                .format(project, e))

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
            self.logger.info('Openshift project build run output: {}/{}\n{}'
                             .format(project, build, output))
            build_id = output.split('"')[-1].rstrip()
            return build_id
        except subprocess.CalledProcessError as e:
            raise OpenshiftError(
                'Unable to run build project build: {}/{}\nError: {}'
                .format(project, build, e))

    def get_build_status(self, project, build_id, status_index=3):
        """Get status of an openshift project build"""
        try:
            output = run_cmd(
                'oc get --namespace {project} build/{build_id} {suffix} | '
                'grep -v STATUS'.format(
                    project=project, build_id=build_id,
                    suffix=self.oc_cmd_suffix),
                shell=True
            )
            self.logger.info('Openshift build status for: {}/{}\n{}'
                             .format(project, build_id, output))
            return output.split()[status_index]
        except subprocess.CalledProcessError as e:
            self.logger.error(
                'Openshift build status fetch error for {}/{}: {}'
                .format(project, build_id, e))
            return ""

    def wait_for_build_status(self, project, build_id, status,
                              empty_retries=10, retry_delay=30,
                              status_index=3):
        """Wait for openshift project build to reach a desired state"""
        self.logger.info('Wait for openshift project build: {}/{} to '
                         'be: {}'.format(project, build_id, status))
        current_status = None
        empty_retry_count = 0
        while True:
            current_status = self.get_build_status(project, build_id,
                                                   status_index=status_index)
            if current_status == status:
                return True
            elif not current_status:
                self.logger.info('Failed to fetch build status for: {}/{}'
                                 .format(project, build_id))
                if empty_retry_count == empty_retries:
                    self.logger.warning(
                        'Exceeded max retries for checking build status for: '
                        '{}/{}. Assuming failure.'.format(project, build_id))
                    return False
                empty_retry_count += 1
                self.logger.info('Retrying {}/{} to check build status for : '
                                 '{}/{}'.format(
                                     empty_retry_count, empty_retries,
                                     project, build_id))
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

    def delete_pods(self, project, build_id):
        """
        Deletes the pods from OpenShift for the provided project and build_id.
        Mainly used by the delivery worker.
        """
        try:
            self.logger.debug("Deleting pods for project build: {}/{}"
                              .format(project, build_id))
            run_cmd(
                'oc delete pods --namespace {project} build/{build_id}'
                ' {suffix}'.format(project=project, build_id=build_id,
                                   suffix=self.oc_cmd_suffix))
            self.logger.info("Deleted pods for project build: {}/{}"
                             .format(project, build_id))
        except subprocess.CalledProcessError as e:
            self.logger.error(
                'Could not delete pods for project build: '
                '{}/{}\n{}'.format(project, build_id, e)
            )
