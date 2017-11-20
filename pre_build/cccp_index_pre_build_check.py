#!/usr/bin/env python
"""Create jenkins jobs from the container-index."""

import os
import subprocess
import sys
import tempfile
from glob import glob

import yaml
from jinja2 import Environment, FileSystemLoader

jjb_defaults_file = 'pre-build-job.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobid', 'git_url', 'appid', 'jobs']


def projectify(
        new_project, appid, jobid, giturl, gitpath, gitbranch,
        desiredtag, prebuild_script):

    new_project[0]['project']['appid'] = appid
    new_project[0]['project']['jobid'] = jobid
    new_project[0]['project']['name'] = appid
    new_project[0]['project']['git_url'] = giturl
    new_project[0]['project']['git_branch'] = gitbranch
    rel_path = "/"
    if gitpath and gitpath != "/":
        rel_path = gitpath if gitpath.startswith("/") else (rel_path + gitpath)
    new_project[0]['project']['rel_path'] = rel_path
    new_project[0]['project']['jobs'] = ['cccp-rundotsh-job']

    if 'rundotshargs' not in new_project[0]:
        new_project[0]['project']['rundotshargs'] = ''
    elif new_project[0]['project']['rundotshargs'] is None:
        new_project[0]['project']['rundotshargs'] = ''

    new_project[0]['project']['desired_tag'] = desiredtag
    new_project[0]['project']['prebuild_script'] = prebuild_script
    return new_project


def get_projects_from_index(indexdlocation):
    projects = []
    for yamlfile in glob(indexdlocation + "/*.yml"):
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
                        try:
                            desiredtag = project['desired-tag'] \
                                if (project['desired-tag'] is not None) \
                                else 'latest'
                        except Exception:
                            desiredtag = 'latest'

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
                            projects.append(
                                projectify(
                                    new_proj, appid, jobid, giturl, gitpath,
                                    gitbranch, desiredtag,
                                    prebuild_script)
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
    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE)

    return proc.communicate()


def main(indexdlocation):
    tempfiles = []
    for project in get_projects_from_index(indexdlocation):
        try:
            env = Environment(loader=FileSystemLoader(
                './'), trim_blocks=True, lstrip_blocks=True)
            template = env.get_template(jjb_defaults_file)
            job_details = template.render(project)

            t = tempfile.mkdtemp()
            generated_filename = os.path.join(
                t,
                'cccp_GENERATED.yaml'
            )
            with open(generated_filename, 'w') as outfile:
                outfile.write(job_details)

            tempfiles.append(generated_filename)
            # run jenkins job builder
            print(
                "Updating jenkins-job of project {0} via file ".format(
                    project))

            myargs = ['jenkins-jobs',
                      '--ignore-cache',
                      'update',
                      generated_filename
                      ]

            _, error = run_command(myargs)
            if error:
                print("Error %s running command %s" % (
                    error, str(myargs)))
                print("Project details: %s ", str(project))
                exit(1)

        except Exception as e:
            print("Project details: %s", str(project))
            print(str(e))
            # if jenkins job update fails, the cccp-index job should fail
            print(sys.exc_info()[0])
            raise


if __name__ == '__main__':
    main(sys.argv[1])
