#!/usr/bin/env python
"""Create jenkins jobs from the container-index."""
import os
import subprocess
import sys
import tempfile
from glob import glob

import yaml

jjb_defaults_file = 'project-defaults.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobid', 'git_url', 'appid', 'jobs']


def projectify(
        new_project, appid, jobid, giturl, gitpath, gitbranch, targetfile,
        dependson_job, dependson_img, notifyemail, desiredtag):

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

    new_project[0]['project']['target_file'] = targetfile
    new_project[0]['project']['depends_on'] = dependson_job
    new_project[0]['project']['depends_on_img'] = dependson_img
    new_project[0]['project']['notify_email'] = notifyemail
    new_project[0]['project']['desired_tag'] = desiredtag
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
                        targetfile = project['target-file']
                        dependson = project['depends-on']
                        notifyemail = project['notify-email']

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
                        dependson_job = ''
                        if dependson is not None:
                            if isinstance(dependson, list):
                                dependson_job = ','.join(dependson)
                            else:
                                dependson_job = str(dependson)
                            dependson_job = dependson_job.replace(
                                ':', '-').replace('/', '-')

                        if dependson_job == '':
                            dependson_job = 'none'

                        # overwrite any attributes we care about see:
                        # projectify
                        projects.append(
                            projectify(
                                new_proj, appid, jobid, giturl, gitpath,
                                gitbranch, targetfile, dependson_job,
                                dependson, notifyemail, desiredtag)
                        )
                    except Exception as e:
                        raise
    return projects


def main(indexdlocation):
    for project in get_projects_from_index(indexdlocation):
        try:
            # workdir = os.path.join(t, gitpath)
            t = tempfile.mkdtemp()
            print "creating: {}".format(t)
            generated_filename = os.path.join(
                t,
                'cccp_GENERATED.yaml'
            )
            # overwrite any attributes we care about see:
            # projectify
            with open(generated_filename, 'w') as outfile:
                yaml.dump(project, outfile)

            # run jenkins job builder
            myargs = ['jenkins-jobs',
                      '--ignore-cache',
                      'update',
                      ':'.join(
                          [jjb_defaults_file, generated_filename])
                      ]
            print myargs
            proc = subprocess.Popen(myargs,
                                    stdout=subprocess.PIPE)
            proc.communicate()

        finally:
            print "Removing {}".format(t)
            # shutil.rmtree(t)


if __name__ == '__main__':
    main(sys.argv[1])
