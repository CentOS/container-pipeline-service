"""
This script parses the container index specified and
creates the Jenkins pipeline projects from entries of index.
"""

import re
import subprocess
import sys
import time
import yaml

from glob import glob


class InvalidPipelineName(Exception):
    """
    Exception to be raised when pipeline name populated doesn't
    confornt to allowed value for openshift template field metadata.name
    """
    pass

class ErrorAccessingIndexEntryAttributes(Exception):
    """
    Exception to be raised when there are errors accessing
    index entry attributes
    """
    pass


def _print(msg):
    """
    _prints the given msg
    """
    print (msg)
    sys.stdout.flush()


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
        Process depends_on for given project based on entry index
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
            self.app_id = self.replace_dot_slash_colon_(entry['app-id'])
            self.job_id = self.replace_dot_slash_colon_(entry['job-id'])

            self.git_url = entry['git-url']
            self.git_path = entry['git-path']
            self.git_branch = entry['git-branch']
            self.target_file = entry['target-file']
            self.build_context = entry.get('build-context', "./")
            self.depends_on = self.process_depends_on(entry['depends-on'])
            self.notify_email = entry['notify-email']
            self.desired_tag = self.process_desired_tag(entry["desired-tag"])
            self.pre_build_context = self.process_pre_build_context(
                entry.get("prebuild-context", None))
            self.pre_build_script = self.process_pre_build_script(
                entry.get("prebuild-script", None))
        except Exception as e:
            raise(ErrorAccessingIndexEntryAttributes(str(e)))

    def get_pipeline_name(self):
        """
        Returns the pipeline name based on appid, jobid and desired_tag
        and also converts it to lower case
        """
        pipeline_name = "{}-{}-{}".format(
            self.app_id, self.job_id, self.desired_tag).lower()

        # pipeline name which becomes value for metadata.name field in template
        # must confront to following regex as per oc
        # We tried to make the string acceptable by converting it to lower case
        # Below we are adding another gate to make sure the pipeline_name is as
        # per requirement, otherwise raising an exception with proper message
        # to indicate the issue
        pipeline_name_regex = ("^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]"
                               "([-a-z0-9]*[a-z0-9])?)*$")
        match = re.match(pipeline_name_regex, pipeline_name)

        if not match:
            msg = ("The pipeline name populated {} can't be used in OpenShift "
                   "template in metadata.name field. ".format(pipeline_name))
            raise(InvalidPipelineName(msg))
        return pipeline_name


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
            _print("Failed to read {}".format(filepath))
            raise(exc)
        else:
            return data

    def read_projects(self):
        """
        Reads yaml entries from container index and returns
        them as list of objects of type Project
        """
        projects = []

        for yamlfile in glob(self.index + "/*.y*ml"):
            # skip index_template
            if "index_template" in yamlfile:
                continue

            app = self.read_yaml(yamlfile)
            for entry in app['Projects']:
                # create a project object here with all properties
                try:
                    project = Project(entry, self.namespace)
                except Exception as e:
                    _print("Error processing index entry {}. Moving on.".format(
                          entry))
                    _print("Error: {}".format(e))
                else:
                    # append to the list of projects
                    projects.append(project)
        return projects


class BuildConfigManager(object):
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

        self.weekly_scan_template_params = """\
-p PIPELINE_NAME=wscan-{pipeline_name} \
-p REGISTRY_URL={registry_url} \
-p NOTIFY_EMAIL={notify_email} \
-p APP_ID={app_id} \
-p JOB_ID={job_id} \
-p DESIRED_TAG={desired_tag} \
-p FROM_ADDRESS={from_address} \
-p SMTP_SERVER={smtp_server}"""

    def list_all_buildConfigs(self):
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

    def apply_build_job(self,
                        project,
                        template_location="seed-job/template.yaml"
                        ):
        """
        Applies the build job template that creates pipeline to build
        image, and trigger first time build as well.
        :param project: Name of project, where the template is to be applied
        :param template_location: The location of the template file.
        """
        oc_process = "oc process -f {0} {1}".format(
            template_location,
            self.seed_template_params
        )

        oc_apply = "oc apply -n {} -f -".format(self.namespace)

        # oc process and oc apply command combined with a shell pipe
        command = oc_process + " | " + oc_apply

        # format the command with project params
        command = command.format(
            git_url=project.git_url,
            git_path=project.git_path,
            git_branch=project.git_branch,
            target_file=project.target_file,
            build_context=project.build_context,
            desired_tag=project.desired_tag,
            depends_on=project.depends_on,
            notify_email=project.notify_email,
            pipeline_name=project.pipeline_name,
            app_id=project.app_id,
            job_id=project.job_id,
            pre_build_context=project.pre_build_context,
            pre_build_script=project.pre_build_script,
            registry_url=self.registry_url,
            from_address=self.from_address,
            smtp_server=self.smtp_server
        )
        # process and apply buildconfig
        output = run_cmd(command, shell=True)
        _print(output)

        # if a buildConfig has config update, oc apply returns
        # "buildconfig.build.openshift.io "$PIPELINE_NAME" configured"
        # possible values are ["unchanged", "created", "configured"]
        # we are looking for "configured" string for updated pipelines
        if "configured" in output:
            _print("{} is updated, starting build..".format(
                project.pipeline_name))
            self.start_build(project.pipeline_name)

    def apply_weekly_scan(self,
                          project,
                          template_location="weekly-scan/template.yaml"
                          ):
        """
        Applies the weekly scan template, creating a pipeline for same
        :param project: The name of the project where the template is to be
        applied.
        :param template_location: The location of template file.
        """
        oc_process = "oc process -f {0} {1}".format(
            template_location,
            self.weekly_scan_template_params
        )

        oc_apply = "oc apply -n {} -f -".format(self.namespace)

        # oc process and oc apply command combined with a shell pipe
        command = oc_process + " | " + oc_apply

        # format the command with project params
        command = command.format(
            git_url=project.git_url,
            git_branch=project.git_branch,
            desired_tag=project.desired_tag,
            notify_email=project.notify_email,
            pipeline_name=project.pipeline_name,
            app_id=project.app_id,
            job_id=project.job_id,
            registry_url=self.registry_url,
            from_address=self.from_address,
            smtp_server=self.smtp_server
        )
        # process and apply buildconfig
        output = run_cmd(command, shell=True)
        _print(output)

    def apply_buildconfigs(self,
                           project,
                           ):
        """
        Given a project object representing a project in container index,
        process the seed-job template for same and oc apply changes
        if needed, also performs `oc start-build` for updated project
        """
        self.apply_build_job(project)
        self.apply_weekly_scan(project)

    def start_build(self, pipeline_name):
        """
        Given a pipeline name, start the build for same
        """
        command = "oc start-build {} -n {}".format(
            pipeline_name, self.namespace)
        _print(run_cmd(command))

    def delete_buildconfigs(self, bcs):
        """
        Deletes the given list of bcs
        """
        command = "oc delete -n {} bc {}"
        for bc in bcs:
            _print("Deleting buildConfig {}".format(bc))
            run_cmd(command.format(self.namespace, bc))

    def list_all_builds(self):
        """
        List all the builds
        """
        command = """\
oc get builds -o name -o template \
--template='{{range .items }}{{.metadata.name}}:{{.status.phase}} {{end}}'"""
        output = run_cmd(command, shell=True)
        return output.strip().split()

    def list_builds_except(
            self,
            status=["Complete", "Failed"],
            filter_builds=["seed-job"]):
        """
        List the builds except the phase(s) provided
        default status=["Complete", "Failed"] <-- This will return
        all the builds except the status.phase in ["Complete", "Failed"].

        If status=[], return all the builds
        """
        if not status:
            return self.list_all_builds()

        conditional = '(ne .status.phase "{}") '
        condition = ''
        for phase in status:
            condition = condition + conditional.format(phase)

        command = """\
oc get builds -o name -o template --template='{{range .items }} \
{{if and %s }} {{.metadata.name}}:{{.status.phase}} \
{{end}}{{end}}'""" % condition
        output = run_cmd(command, shell=True)
        output = output.strip().split(' ')
        output = [each for each in output
                  if not each.startswith(tuple(filter_builds))
                  and each]
        return output


class Index(object):
    """
    The orchestrator class to process operations
    in container index.
    """

    def __init__(self, index, registry_url, namespace,
                 from_address, smtp_server):
        # create index reader object
        self.index_reader = IndexReader(index, namespace)
        # create bc_manager object
        self.bc_manager = BuildConfigManager(
            registry_url, namespace, from_address, smtp_server)
        self.infra_projects = ["seed-job"]

    def find_stale_jobs(self, oc_projects, index_projects):
        """
        Given oc projects and index projects, figure out stale
        projects and return
        """
        # diff existing oc projects from index projects

        return list(set(oc_projects) - set(index_projects))

    def run(self):
        """
        Orchestrate container index processing
        """
        # list all jobs in index, list of project objects
        index_projects = self.index_reader.read_projects()

        _print("Number of projects in index {}".format(len(index_projects)))

        # list existing jobs in openshift
        oc_projects = self.bc_manager.list_all_buildConfigs()

        # filter out infra projects and return only pipeline name
        # bc names are like buildconfig.build.openshift.io/app_id-job_id-dt
        oc_projects = [bc.split("/")[1] for bc in oc_projects
                       if bc.split("/")[1] not in self.infra_projects]

        _print("Number of projects in OpenShift {}".format(len(oc_projects)))

        # names of pipelines for all projects in container index
        index_project_names = [project.pipeline_name for project in
                               index_projects]
        # Adding weekly scan project names
        index_project_names_with_wscan = []
        for item in index_project_names:
            index_project_names_with_wscan.append(item)
            index_project_names_with_wscan.append("wscan-" + item)

        # find stale projects based on pipeline-name
        stale_projects = self.find_stale_jobs(
            oc_projects, index_project_names_with_wscan
        )

        if stale_projects:
            _print("List of stale projects:\n{}".format(
                "\n".join(stale_projects)))
            # delete all the stal projects/buildconfigs
            self.bc_manager.delete_buildconfigs(stale_projects)

        _print("Number of projects to be updated/created: {}".format(
            len(index_projects)))

        self.batch_process_projects(index_projects)

    def batch(self, target, batch_size):
        """
        Returns a generator object yielding chunks of list
        of length=batch_size from target list
        """
        for i in range(0, len(target), batch_size):
            yield target[i:i + batch_size]

    def batch_process_projects(self,
                               index_projects, batch_size=5, poll_cycle=120):
        """
        Given a list of projects, oc apply the buildconfigs
        in batches and oc apply the weekly scan jobs at the end
        """
        # Split the projects to process in equal sized chunks
        generator_obj = self.batch(index_projects, batch_size)

        interval_cycle = 1
        for batch in generator_obj:
            outstanding_builds = True
            while outstanding_builds:
                # Check if builds are in status.phase other than Complete
                # or Failed. We dont care about builds which are failed
                # or complete to queue up next batch of jobs to process
                outstanding_builds = self.bc_manager.list_builds_except(
                    status=["Complete", "Failed"],
                    filter_builds=self.infra_projects)

                if outstanding_builds:
                    _print("Waiting for completion of builds {}\n".format(
                        outstanding_builds))
                    time.sleep(poll_cycle)

            _print("Processing projects batch: {}\n".format(
                [each.pipeline_name for each in batch]))

            for project in batch:
                # oc process and oc apply to all fresh and existing jobs
                try:
                    self.bc_manager.apply_build_job(project)
                except Exception as e:
                    _print("Error applying/creating build config for {}. "
                           "Moving on.".format(project.pipeline_name))
                    _print("Error: {}".format(str(e)))
                else:
                    # grace period between configuring jobs
                    time.sleep(interval_cycle)

        _print("Processing weekly scan projects..")
        for project in index_projects:
            try:
                self.bc_manager.apply_weekly_scan(project)
            except Exception as e:
                _print("Error applying/creating weekly scan build config "
                       "for {}. Moving on.".format(project.pipeline_name))
                _print("Error: {}".format(str(e)))
            else:
                # grace period between configuring jobs
                time.sleep(interval_cycle)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        _print("Incomplete set of input variables, please refer README.")
        sys.exit(1)

    index = sys.argv[1].strip()
    registry_url = sys.argv[2].strip()
    namespace = sys.argv[3].strip()
    from_address = sys.argv[4].strip()
    smtp_server = sys.argv[5].strip()

    index_object = Index(index, registry_url, namespace,
                         from_address, smtp_server)

    index_object.run()
