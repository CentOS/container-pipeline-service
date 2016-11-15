#!/usr/bin/env python
import os
import yaml
import shutil
import subprocess
import tempfile
import warnings
import sys
from glob import glob

jjb_defaults_file = 'project-defaults.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobid', 'git_url', 'appid', 'jobs']


def projectify(
      new_project, appid, jobid, giturl, gitpath, gitbranch, targetfile,
      dependson, notifyemail, desiredtag):

    new_project[0]['project']['appid'] = appid
    new_project[0]['project']['jobid'] = jobid
    new_project[0]['project']['git_url'] = giturl
    new_project[0]['project']['git_branch'] = gitbranch
    new_project[0]['project']['rel_path'] = ('/' + gitpath) \
        if (gitpath and not gitpath.startswith('/')) else '/'
    new_project[0]['project']['jobs'] = ['cccp-rundotsh-job']

    if 'rundotshargs' not in new_project[0]:
        new_project[0]['project']['rundotshargs'] = ''
    elif new_project[0]['project']['rundotshargs'] is None:
        new_project[0]['project']['rundotshargs'] = ''

    new_project[0]['project']['target_file'] = targetfile
    new_project[0]['project']['depends_on'] = dependson
    new_project[0]['project']['notify_email'] = notifyemail
    new_project[0]['project']['desired_tag'] = desiredtag
    return new_project


def main(indexdlocation):

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
                        t = tempfile.mkdtemp()
                        print "creating: {}".format(t)
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
                        except Exception as e:
                            desiredtag = 'latest'

                        # workdir = os.path.join(t, gitpath)
                        generated_filename = os.path.join(
                            t,
                            'cccp_GENERATED.yaml'
                        )
                        new_proj = [{'project': {}}]

                        appid = appid.replace(
                                '_', '-').replace('/', '-').replace('.', '-')
                        jobid = jobid.replace(
                                '_', '-').replace('/', '-').replace('.', '-')

                        # overwrite any attributes we care about see: projectify
                        with open(generated_filename, 'w') as outfile:
                            yaml.dump(projectify(
                                new_proj, appid, jobid, giturl, gitpath,
                                gitbranch, targetfile, dependson, notifyemail,
                                desiredtag),
                                outfile)

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
