#!/usr/bin/env python
"""Create jenkins jobs from the container-index."""
import os
import subprocess
import sys
import tempfile
from glob import glob

import yaml

jjb_defaults_file = 'project-defaults.yml'

# pathname of file having all project names
# this file will be generated after first run
# and will reside in same directory as of this python file
projects_list = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "all_projects_names.txt"
)

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
            index_yaml = yaml.load(stream)
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
                        print e
                        raise
    return projects


def export_new_project_names(projects_names):
    """
    Exports the name of project
    """
    # opens the file defined at the start of this script
    projects_names = "\n".join(projects_names)
    with open(projects_list, "w") as fin:
        fin.write(projects_names)


def get_old_project_list():
    """
    This function retuns the list of projects that were indexed
    during last run of cccp-index job. It returns [] empty list
    if it can not find the project list.
    """
    if not os.path.exists(projects_list):
        print "%s does not exist. This is first run or file is absent." \
            % projects_list
        return []
    with open(projects_list) as fin:
        old_projects = fin.read()
    return list(set(old_projects.strip().split("\n")))


def find_stale_projects(old, new):
    """
    This function diffs the old project list with new project
    list. And returns the list of project names to be deleted
    """
    return list(set(old) - set(new))


def delete_stale_projects_on_jenkins(stale_projects):
    """
    This function deletes the stale entries at jenkins that
    are no longer valid. If there is any issue/exception, it
    bypasses by printing the error.
    """
    for project in stale_projects:
        myargs = ["jenkins-jobs", "delete", project]
        # print either output or error
        print run_command(myargs)


def delete_stale_projects_on_openshift():
    """
    Stale projects found on jenkins need to be deleted
    accordingly on OpenShift as well. This function maps
    the project names from jenkins to openshift and deletes them.
    (see delete_stale_projects_on_jenkins function)
    """
    pass


def run_command(command):
    """
    runs the given shell command using subprocess
    """
    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE)

    return proc.communicate()


def main(indexdlocation):
    new_projects_names = []
    for project in get_projects_from_index(indexdlocation):
        try:
            # workdir = os.path.join(t, gitpath)
            t = tempfile.mkdtemp()
            # print "creating: {}".format(t)
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
            run_command(myargs)

            new_projects_names.append(
                str(project[0]["project"]["appid"]) + "-" +
                str(project[0]["project"]["jobid"]) + "-" +
                str(project[0]["project"]["desired_tag"])
            )
        finally:
            pass
    # get list of old projects
    old_projects = get_old_project_list()

    # find stale projects
    stale_projects = find_stale_projects(
        old_projects,
        list(set(new_projects_names))
    )

    print stale_projects

    # delete stale entries at jenkins
    delete_stale_projects_on_jenkins(stale_projects)

    # delete stale entries at openshift
    delete_stale_projects_on_openshift()

    # export the current projects_list in file
    export_new_project_names(new_projects_names)

if __name__ == '__main__':
    main(sys.argv[1])
