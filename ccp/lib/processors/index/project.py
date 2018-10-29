"""
Contains the model for project
"""

import re

from ccp.lib.exceptions import ErrorAccessingIndexEntryAttributes, \
    InvalidPipelineName


class Project(object):
    """
    Class for storing and processing a container index project
    """

    def __init__(self, entry, namespace):
        """
        Initialize project object with an entry in container index
        :param entry: The entry to process into a project
        :type entry: dict
        :param namespace: The OpenShift namespace to which this belongs
        :type namespace: str
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

    @staticmethod
    def replace_dot_slash_colon_(value):
        """
        Given a value with either dot slash or underscore,
        replace each with hyphen
        :param value: The value that needs to be normalised
        :type value: str
        :return Normalised string wihout ., / or :
        :rtype str
        """
        return value.replace("_", "-").replace("/", "-").replace(
            ".", "-").replace(":", "-")

    def process_depends_on(self, depends_on=None):
        """
        Process depends_on for given project based on entry index
        and namespace
        :param depends_on: Default None: The list or single entry on which this
        project depends on
        :type depends_on: Union[list, str]
        :return Jenkins understandable format of project dependencies
        :rtype str
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

    @staticmethod
    def process_desired_tag(desired_tag=None):
        """
        Process desired_tag for given project
        :param desired_tag: Default None: The project desired tag to process
        :type desired_tag: str
        :return The processed desired tag
        :rtype str
        """
        if not desired_tag:
            return "latest"
        return desired_tag

    @staticmethod
    def process_pre_build_script(prebuild_script=None):
        """
        Process prebuild_script for given project
        :param prebuild_script: Default None: The prebuild script to process
        :type prebuild_script str
        :return The processed prebuild script
        :rtype str
        """
        if not prebuild_script:
            return None
        return prebuild_script

    @staticmethod
    def process_pre_build_context(prebuild_context=None):
        """
        Process prebuild_context for given project
        :param prebuild_context: Default None: The prebuild context to process
        :type prebuild_context: str
        :return The processed prebuild context
        :rtype str
        """
        if not prebuild_context:
            return None
        return prebuild_context

    def load_project_entry(self, entry):
        """
        Loads a container index entry in class objects
        :param entry: The entry to process and create a model out of
        :type entry: dict
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
        :return The name of the pipeline
        :rtype str
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
