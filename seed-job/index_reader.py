"""
This script parses the container index specified and
creates the Jenkins pipeline projects from entries of index.
"""

import os
import subprocess
import sys
import yaml

from glob import glob


def run_cmd(cmd, shell=False):
    """
    Runs the given shell command

    :param cmd: Command to run
    :param shell: Whether to run raw shell commands with '|' and redirections
    :type cmd: str
    :type shell: boolean

    :return: Command output
    :rtype: str
    :raises: subprocess.CalledProcessError
    """
    if shell:
        return subprocess.check_output(cmd, shell=True)
    else:
        return subprocess.check_output(cmd.split(), shell=False)


class Project(object):
    """
    Class for storing and processing a container index project
    """

    def __init__(self, entry, namespace):
        """
        Initialize project object with an entry in container index
        """
        self.namespace = namespace
        self.load_project_entry(entry)
        self.pipeline_name = self.get_pipeline_name()

    def __str__(self):
        """
        Returns the string representation of the project object
        It returns the pipeline-name, which is constructed
        based on parameters of the project indexed.
        """
        return self.pipeline_name

    def replace_dot_slash_colon_(self, value):
        """
        Given a value with either dot slash or underscore,
        replace each with hyphen
        """
        return value.replace("_", "-").replace("/", "-").replace(
            ".", "-").replace(":", "-")

    def process_depends_on(self, depends_on=None):
        """
        Process dependson for given project based on entry index
        and namespace
        """
        if not depends_on or depends_on == "null":
            return None

        if isinstance(depends_on, list):
            return ",".join("{}-{}".format(
                self.namespace,
                self.replace_dot_slash_colon_(d))
                for d in depends_on)
        else:
            return "{}-{}".format(
                self.namespace,
                self.replace_dot_slash_colon_(depends_on))

    def process_desired_tag(self, desired_tag=None):
        """
        Process desired_tag for given project
        """
        if not desired_tag:
            return "latest"
        return desired_tag

    def process_pre_build_script(self, prebuild_script=None):
        """
        Process prebuild_script for given project
        """
        if not prebuild_script:
            return None
        return prebuild_script

    def process_pre_build_context(self, prebuild_context=None):
        """
        Process prebuild_context for given project
        """
        if not prebuild_context:
            return None
        return prebuild_context

    def load_project_entry(self, entry):
        """
        Loads a container index entry in class objects
        """
        try:
            self.appid = self.replace_dot_slash_colon_(entry['app-id'])
            self.jobid = self.replace_dot_slash_colon_(entry['job-id'])

            self.giturl = entry['git-url']
            self.gitpath = entry['git-path']
            self.gitbranch = entry['git-branch']
            self.targetfile = entry['target-file']
            self.build_context = entry.get('build-context', "./")
            self.dependson = self.process_depends_on(entry['depends-on'])
            self.notifyemail = entry['notify-email']
            self.desiredtag = self.process_desired_tag(entry["desired-tag"])
            self.pre_build_context = self.process_pre_build_context(
                entry.get("prebuild-context", None))
            self.pre_build_script = self.process_pre_build_script(
                entry.get("prebuild-script", None))
        except Exception as e:
            print ("Error processing container index entry.")
            raise(e)

    def get_pipeline_name(self):
        """
        Returns the pipeline name based on the project object values
        """
        return "{}-{}-{}".format(self.appid, self.jobid, self.desiredtag)


class IndexReader(object):
    """
    Class for reading container index and utilities
    """

    def __init__(self, index, namespace):
        """
        Initialize class variable with index location
        """
        self.index = index
        self.namespace = namespace

    def read_yaml(self, filepath):
        """
        Read the YAML file at specified location

        return the yaml data on success
        raise an exception upon failure reading/load the file
        """
        try:
            with open(filepath) as fin:
                data = yaml.load(fin, Loader=yaml.BaseLoader)
        except yaml.YAMLError as exc:
            raise(exc)
        else:
            return data

    def read_projects(self):
        """
        Reads the projects from given container index
        """
        projects = []

        for yamlfile in glob(self.index + "/*.y*ml"):
            # skip index_template
            if "index_template" in yamlfile:
                continue

            app = self.read_yaml(yamlfile)
            for entry in app['Projects']:
                # create a project object here with all properties
                project = Project(entry, self.namespace)
                # append to the list of projects
                projects.append(project)

        return projects


class DeploymentConfigManager(object):
    """
    This class represents utilities to manage
    deployment configs on openshift as used
    by pipeline service
    """

    def __init__(self, registry_url, namespace, from_address, smtp_server):
        self.registry_url = registry_url
        self.namespace = namespace
        self.from_address = from_address
        self.smtp_server = smtp_server
        self.seed_template_params = """\
-p GIT_URL={git_url} \
-p GIT_PATH={git_path} \
-p GIT_BRANCH={git_branch} \
-p TARGET_FILE={target_file} \
-p BUILD_CONTEXT={build_context} \
-p DESIRED_TAG={desired_tag} \
-p DEPENDS_ON={depends_on} \
-p NOTIFY_EMAIL={notify_email} \
-p PIPELINE_NAME={pipeline_name} \
-p APP_ID={app_id} \
-p JOB_ID={job_id} \
-p PRE_BUILD_CONTEXT={pre_build_context} \
-p PRE_BUILD_SCRIPT={pre_build_script} \
-p REGISTRY_URL={registry_url} \
-p FROM_ADDRESS={from_address} \
-p SMTP_SERVER={smtp_server}"""

    def list_all_buildconfigs(self):
        """
        List all available buildConfigs
        returns list of buildConfigs available
        """
        command = "oc get bc -o name -n {}".format(self.namespace)
        bcs = run_cmd(command)
        if not bcs.strip():
            return []
        else:
            return bcs.strip().split("\n")

    def oc_apply_seedjob_template_command(
            self, template_location="seed-job/template.yml"):
        """
        Returns the oc process and oc apply commands with parameters
        to process seed-job/template.yml
        """
        oc_apply = "oc apply -n {} -f -".format(self.namespace)
        oc_process = "oc process -f {0} {1}".format(
            template_location,
            self.seed_template_params
        )
        return oc_process + "|" + oc_apply

    def apply_buildconfigs(self, project):
        """
        Given a project object representing a project in container index,
        process the seed-job template for same and oc apply changes
        """
        # get the oc process and oc apply command
        command = self.oc_apply_seedjob_template_command()
        # format the command with project params
        command = command.format(
            git_url=project.giturl,
            git_path=project.gitpath,
            git_branch=project.gitbranch,
            target_file=project.targetfile,
            build_context=project.build_context,
            desired_tag=project.desiredtag,
            depends_on=project.dependson,
            notify_email=project.notifyemail,
            pipeline_name=project.pipeline_name,
            app_id=project.appid,
            job_id=project.jobid,
            pre_build_context=project.pre_build_context,
            pre_build_script=project.pre_build_script,
            registry_url=self.registry_url,
            from_address=self.from_address,
            smtp_server=self.smtp_server
        )
        # process and apply buildconfig
        output = run_cmd(command, shell=True)
        print (output)


class Index(object):
    """
    The orchestrator class to process operations
    in container index.
    """

    def __init__(self, index, registry_url, namespace,
                 from_address, smtp_server):
        # create index reader object
        self.index_reader = IndexReader(index, namespace)
        # create dc_manager object
        self.dc_manager = DeploymentConfigManager(
            registry_url, namespace, from_address, smtp_server)

    def run(self):
        # list all jobs in index
        # list existing jobs
        # figure out stale jobs
        # figure out new jobs
        # delete stale jobs
        # create new jobs
        # update existing jobs
        projects = self.index_reader.read_projects()
        for project in projects:
            self.dc_manager.apply_buildconfigs(project)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit(1)

    index = sys.argv[1].strip()
    registry_url = sys.argv[2].strip()
    namespace = sys.argv[3].strip()
    from_address = sys.argv[4].strip()
    smtp_server = sys.argv[5].strip()

    index_object = Index(index, registry_url, namespace,
                         from_address, smtp_server)

    index_object.run()
