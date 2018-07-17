"""
This script parses the container index specified and
creates the Jenkins pipeline projects from entries of index.
"""

import os
import subprocess
import sys
import yaml


def run_cmd(cmd):
    """
    Runs the given command and returns the output and error
    """
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).communicate()


class Project(object):
    """
    Class for storing and processing a container index project
    """

    def __init__(self, entry, namespace):
        """
        Initialize project object with an entry in container index
        """
        self.load_project_entry(entry)
        self.namespace = namespace

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
        if not depends_on:
            return None
        return "{}-{}".format(self.namespace,
                              self.replace_dot_slash_colon_(depends_on)
                              )
        """
        # TODO: process multiple dependson values
            if dependson is not None:
                if isinstance(dependson, list):
                    dependson_job = ','.join(dependson)
                else:
                    dependson_job = str(dependson)
                dependson_job = dependson_job.replace(
                    ':', '-').replace('/', '-')

            if dependson_job == '':
                dependson_job = 'none'
        """

    def process_desired_tag(self, desired_tag=None):
        """
        Process desired_tag for given project
        """
        if not desired_tag:
            return "latest"
        return desired_tag

    def process_build_context(self, build_context=None):
        """
        Process build_context for given project
        """
        if not build_context:
            return "./"
        return build_context

    def process_prebuild_script(self, prebuild_script=None):
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
            self.dependson = self.process_depends_on(entry['depends-on'])
            self.notifyemail = entry['notify-email']
            self.desiredtag = self.process_desired_tag(entry["desired-tag"])
            self.build_context = self.process_build_context(
                entry["build-context"])
            self.pre_build_context = self.process_pre_build_context(
                entry["prebuild-context"])
            self.pre_build_script = self.process_pre_build_script(
                entry["prebuild-script"])
        except Exception as e:
            print ("Error processing container index entry.")
            raise(e)

    def pipeline_name(self):
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
