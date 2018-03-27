#!/usr/bin/env python
"""Create jenkins jobs from the container-index."""

import logging
import os
import subprocess
import sys
import tempfile
from glob import glob

import yaml

from container_pipeline.lib import dj  # noqa
from container_pipeline.lib.log import load_logger
from container_pipeline.lib.settings import LOGS_BASE_DIR
from container_pipeline.utils import form_targetfile_link
from container_pipeline.models import Project

# Fix integration of django with other Python scripts.

# populate container_pipeline module path
cp_module_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "container_pipeline"
)
# add path of modules to system path for imports
sys.path.append(os.path.dirname(cp_module_path))
sys.path.append(cp_module_path)
jjb_defaults_file = 'project-defaults.yml'
logger = logging.getLogger('jenkins')

# pathname of file having all project names
# this file will be generated after first run
# and will reside in NFS logs directory to persist across redeployments
projects_list = os.path.join(
    LOGS_BASE_DIR,
    "all_projects_names.txt"
)

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobid', 'git_url', 'appid', 'jobs']


def projectify(
        new_project, appid, jobid, giturl, gitpath, gitbranch, targetfile,
        dependson_job, dependson_img, notifyemail, desiredtag, build_context):

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
    new_project[0]['project']['build_context'] = build_context
    return new_project


def get_projects_from_index(indexdlocation):
    projects = []
    for yamlfile in glob(indexdlocation + "/*.y*ml"):
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

                        build_context = project.get("build-context")
                        if not build_context:
                            build_context = "./"

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

                        if project.get('prebuild-script'):
                            giturl = "https://github.com/bamachrn/"\
                                "cccp-pre-build-code"
                            gitbranch = "{}-{}-{}".format(appid,
                                                          jobid, desiredtag)

                        # overwrite any attributes we care about see:
                        # projectify
                        projects.append(
                            projectify(
                                new_proj, appid, jobid, giturl, gitpath,
                                gitbranch, targetfile, dependson_job,
                                dependson, notifyemail, desiredtag,
                                build_context)
                        )
                    except Exception as e:
                        logger.critical("Failed to projectify %s" %
                                        str(project))
                        logger.critical(str(e))
                        logger.critical(sys.exc_info()[0])
                        raise
    return projects


def export_new_project_names(projects_names):
    """
    Exports the name of project
    """
    # opens the file defined at the start of this script
    projects_names = "\n".join(projects_names)
    try:
        with open(projects_list, "w") as fin:
            fin.write(projects_names)
        # change the mod of file so that jenkins user can edit it
        logger.info("Exported current projects list to file %s", projects_list)
        logger.debug("Changing file permission 0777 of file %s", projects_list)
        run_command(["chmod", "0777", projects_list])
    except IOError as e:
        logger.error("Failed to export project names to file %s" %
                     projects_list)
        logger.error("I/O Error {0}:{1}".format(e.errno, e.strerror))
    except Exception as e:
        logger.error("Failed to export project names to file %s" %
                     projects_list)
        logger.error("Unexpected error:%s", sys.exc_info()[0])


def get_old_project_list():
    """
    This function retuns the list of projects that were indexed
    during last run of cccp-index job. It returns [] empty list
    if it can not find the project list.
    """
    if not os.path.exists(projects_list):
        logger.warning("%s is absent. It could be first run.", projects_list)
        return []
    try:
        with open(projects_list) as fin:
            old_projects = fin.read()
        return list(set(old_projects.strip().split("\n")))
    except IOError as e:
        logger.error("Failed to read project names from file: %s",
                     projects_list)
        logger.error("I/O Error {0}:{1}".format(e.errno, e.strerror))
        return []
    except Exception as e:
        logger.error("Failed to read project names from file: %s",
                     projects_list)
        logger.error("Unexpected error: %s", sys.exc_info()[0])
        return []


def get_new_project_list(indexdlocation):
    """
    This function returns list of projects in the container-index. It's called
    get_new_project_list because it takes a fresh look at container-index every
    time. It requires a path to the directory containing container-index and
    returns a list
    """
    new_projects_names = []
    for project in get_projects_from_index(indexdlocation):
        new_projects_names.append(
            str(project[0]["project"]["appid"]) + "/" +
            str(project[0]["project"]["jobid"]) + ":" +
            str(project[0]["project"]["desired_tag"])
        )
    return new_projects_names


def create_or_update_project_on_jenkins(indexdlocation):
    """
    This function creates new project(s) on Jenkins if it finds new entry added
    to container-index. It requires a path to the directory container
    container-index.
    """
    for project in get_projects_from_index(indexdlocation):
        try:
            t = tempfile.mkdtemp()
            generated_filename = os.path.join(
                t,
                'cccp_GENERATED.yaml'
            )
            # overwrite any attributes we care about see:
            # projectify
            with open(generated_filename, 'w') as outfile:
                yaml.dump(project, outfile)
            # run jenkins job builder
            logger.info(
                "Updating jenkins-job of project {0} via file {1}".format(
                    project, outfile))
            myargs = ['jenkins-jobs',
                      '--ignore-cache',
                      'update',
                      ':'.join(
                          [jjb_defaults_file, generated_filename])
                      ]
            _, error = run_command(myargs)
            if error:
                logger.critical("Error %s running command %s" % (
                    error, str(myargs)))
                logger.critical("Project details: %s ", str(project))
                exit(1)
                p, c = Project.objects.get_or_create(
                    name='{}-{}-{}'.format(
                        project[0]['project']['appid'],
                        project[0]['project']['jobid'],
                        project[0]['project']['desired_tag'])
                )
                p.target_file_link = form_targetfile_link(
                    project[0]['project']['git_url'],
                    project[0]['project']['rel_path'],
                    project[0]['project']['git_branch'],
                    project[0]['project']['target_file']
                )
                p.save()

        except Exception as e:
            logger.critical("Error updating jenkins job via file %s",
                            generated_filename)
            logger.critical("Project details: %s", str(project))
            logger.critical(str(e))
            # if jenkins job update fails, the cccp-index job should fail
            logger.critical(sys.exc_info()[0])
            raise


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
        project = project.replace('/', '-').replace(':', '-')
        myargs = ["jenkins-jobs", "delete", project]
        # print either output or error
        _, error = run_command(myargs)
        if error:
            logger.critical("Failed to delete project %s. Exiting..", project)
            logger.critical(sys.exc_info()[0])
            exit(1)
            # if a job fails to be deleted from jenkins it will create issues
            # cccp-index job at jenkins needs to fail and be notified
    logger.info("Deleted stale projects successfully.")


def run_command(command):
    """
    runs the given shell command using subprocess
    """
    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE)

    return proc.communicate()


def main(indexdlocation):
    new_projects_names = get_new_project_list(indexdlocation)
    create_or_update_project_on_jenkins(indexdlocation)

    # get list of old projects
    old_projects = get_old_project_list()

    # find stale projects
    stale_projects = find_stale_projects(
        old_projects,
        list(set(new_projects_names))
    )
    logger.info("List of stale projects: %s ", str(stale_projects))

    if stale_projects:
        # delete stale entries at jenkins
        logger.debug("Deleting stale projects.")
        delete_stale_projects_on_jenkins(stale_projects)
    else:
        logger.info("No stale projects in Jenkins.")

    # export the current projects_list in file
    logger.debug("Exporting current project names.")
    export_new_project_names(new_projects_names)


if __name__ == '__main__':
    load_logger()
    logger = logging.getLogger('jenkins')
    main(sys.argv[1])
