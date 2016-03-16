#!/usr/bin/env python
import os
import yaml
import shutil
import subprocess
import tempfile
import warnings
import sys

jjb_defaults_file = 'project-defaults.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobname', 'git_url', 'ci_project', 'jobs']


def projectify(project,appid,jobid,giturl,gitpath,gitbranch,notifyemail):
    project['namespace'] = appid
    project['jobname'] = jobid
    project['ci_project'] = appid
    project['git_url'] = giturl
    project['rel_path'] = ('/' + gitpath) \
        if (gitpath and not gitpath.startswith('/')) else '/'
    project['jobs'] = ['cccp-rundotsh-job']
    
    if 'rundotshargs' not in project:
        project['rundotshargs'] = ''
    elif project['rundotshargs'] is None:
        project['rundotshargs'] = ''
    
    return project

def main(yamlfile):
    stream = open(yamlfile,'r')
    index_yaml = yaml.load(stream)
    stream.close()
    #print index_yaml['Projects']
  
    for project in index_yaml['Projects']:
        if(project['git-url'] == None):
            continue
        else:
            try:
                t= tempfile.mkdtemp()
                print "creating: {}".format(t)
                appid = project['app-id']
                jobid = project['job-id']
                giturl = project['git-url']
                gitpath = project['git-path'] if (project['git-path'] != None) else ''
                gitbranch = project['git-branch']
                notifyemail = project['notify-email']
    		
                workdir = os.path.join(t, gitpath)
                generated_filename = os.path.join(
                    workdir,
                    'cccp_GENERATED.yaml'
                )   

                # overwrite any attributes we care about see: projectify
                with open(generated_filename, 'w') as outfile:
                    yaml.dump(projectify(project,appid,jobid,giturl,gitpath,gitbranch,notifyemail), outfile)

                # run jenkins job builder
                myargs = ['jenkins-jobs',
                          '--ignore-cache',
                          'update',
                          ':'.join([jjb_defaults_file, generated_filename])
                         ]
                print myargs
                proc = subprocess.Popen(myargs,
                                        stdout=subprocess.PIPE)
                proc.communicate()

            finally:
                print "Removing {}".format(t)
                shutil.rmtree(t)


if __name__ == '__main__':
    main(sys.argv[1])
