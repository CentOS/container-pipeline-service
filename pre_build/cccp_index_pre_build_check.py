#!/usr/bin/env python
"""
This class is for generating pre-build jobs in ci.centos.org.

It takes contianer-index as input, parses through all the YMLs.
Once entries with prebuild_script parameter found, this class generates
one job config to be used for setting up prebuild-jobs in ci.centos.org.
Then it runs the jenkins-job builder command for creating the job in
ci.centos.org jenkins.
"""

import random
import string
import subprocess
import sys
from glob import glob

import yaml
from jinja2 import Environment, FileSystemLoader

jjb_defaults_file = 'pre-build-job.yml'


def projectify(
        new_project, appid, jobid, giturl, gitpath, gitbranch,
        desiredtag, prebuild_script, prebuild_context):
    """
    Projectifying container-index entry to be used for generating job template.

    This function puts all the parameter from container-index entry to a
    dictory named project. this dictionary later used for rendering the job
    template.
    """
    new_project[0]['project']['appid'] = appid
    new_project[0]['project']['jobid'] = jobid
    new_project[0]['project']['name'] = appid
    new_project[0]['project']['git_url'] = giturl
    new_project[0]['project']['git_branch'] = gitbranch
    rel_path = "/"
    if gitpath and gitpath != "/":
        rel_path = gitpath if gitpath.startswith("/") else (rel_path + gitpath)
    new_project[0]['project']['rel_path'] = rel_path
    new_project[0]['project']['desired_tag'] = desiredtag
    new_project[0]['project']['prebuild_script'] = prebuild_script
    new_project[0]['project']['prebuild_context'] = prebuild_context
    return new_project


def get_projects_from_index(indexdlocation):
    """
    Reading all the entries of contianer-index.

    This function reads all the entry from container-index ymls and puts
    them in array if it has parameter prebuild_script.
    """
    projects = []
    for yamlfile in glob(indexdlocation + "/*.yaml"):
        if "index_template" not in yamlfile:
            stream = open(yamlfile, 'r')
            index_yaml = yaml.load(stream, Loader=yaml.BaseLoader)
            stream.close()
            # print index_yaml['Projects']

            for project in index_yaml['Projects']:
                if(project['git-url'] is None):
                    continue
                else:
                    try:
                        appid = project['app-id']
                        jobid = project['job-id']
                        giturl = project['git-url']
                        gitpath = project['git-path'] \
                            if (project['git-path'] is not None) else ''
                        gitbranch = project['git-branch']
                        desiredtag = 'latest' if not project.get(
                            'desired-tag') else project.get('desired-tag')
                        desiredtag = str(desiredtag)

                        new_proj = [{'project': {}}]

                        appid = appid.replace(
                            '_', '-').replace('/', '-').replace('.', '-')
                        jobid = jobid.replace(
                            '_', '-').replace('/', '-').replace('.', '-')

                        # Set the pre-build data if available
                        prebuild_script = 'none' if not project.get(
                            'prebuild-script') else project['prebuild-script']

                        # Check for the project only if it requires pre-build
                        if(prebuild_script != 'none'):
                            prebuild_context = project['prebuild-context']
                            projects.append(
                                projectify(
                                    new_proj, appid, jobid, giturl, gitpath,
                                    gitbranch, desiredtag,
                                    prebuild_script, prebuild_context)
                            )
                    except Exception as e:
                        print("Failed to projectify %s" %
                              str(project))
                        print("Error is : %s %s" % (str(e), sys.exc_info()[0]))
                        raise
    return projects


def run_command(command):
    """
    runs the given shell command using subprocess
    """
    print("Running command: %s" % str(command))
    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE)

    return proc.communicate()


def main(indexdlocation):
    """
    Conververting index entries to jenkins job configs.

    This function takes project dictionary generated from container-index as
    input, renders it to the prebuild-job config and creates jobtemplates to
    be used for creating the pre-build jobs in ci.centos.org.
    """
    tempfiles = []
    job_template_list = open('job_template_list.txt', 'w')
    for project in get_projects_from_index(indexdlocation):
        try:
            print("Processing project with details: %s" % str(project))
            try:
                env = Environment(loader=FileSystemLoader(
                    './'), trim_blocks=True, lstrip_blocks=True)
                template = env.get_template(jjb_defaults_file)
                job_details = template.render(project[0]['project'])
            except Exception as e:
                print("Error template is not updated: %s" % str(e))

            try:
                pre_text = ''.join(random.sample(
                    string.lowercase + string.digits, 10))
                generated_filename = "%s_%s" % (pre_text,
                                                'cccp_GENERATED.yaml'
                                                )
                with open(generated_filename, 'w') as outfile:
                    outfile.write(job_details)
                    outfile.flush()
                tempfiles.append(generated_filename)
            except Exception as e:
                print("Error job_details could not be updated %s" % str(e))

            # write the job template names to file so that these can be
            # processed by jenkins builder to create jobs
            job_template_list.write("%s\n" % generated_filename)
            job_template_list.flush()
        except Exception as e:
            print("Project details: %s" % str(project))
            print(str(e))
            # if jenkins job update fails, the cccp-index job should fail
            print(sys.exc_info()[0])
            raise
    job_template_list.close()


if __name__ == '__main__':
    main(sys.argv[1])
