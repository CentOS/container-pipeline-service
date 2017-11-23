import hashlib
import json
import logging
import os
import urllib2


def get_job_name(job_details):
    """Get jenkins job name from job_detials"""
    namespace = str(job_details['appid']) + "-" + str(job_details['jobid']) + \
        "-" + str(job_details['desired_tag'])
    return namespace


def get_job_hash(namespace):
    """Returns hash value for the namespace"""
    return hashlib.sha224(namespace).hexdigest()


def get_project_name(job):
    """Get project name from job data"""
    return '{}-{}-{}'.format(job['appid'], job['jobid'], job['desired_tag'])


def parse_json_response(response):
    """Parses the json response provided to it to determin"""
    try:
        cause = response['actions'][0]['causes'][0]['shortDescription']

        if cause == 'Started by an SCM change':
            return 'Git commit {}'.format(
                response['actions'][2]['lastBuiltRevision']['SHA1']
            )
        elif 'Started by upstream project' in cause:
            return 'Change in upsream project {}'.format(
                response['actions'][0]['causes'][0]['shortDescription'].split(
                    '"')[1]
            )
        elif 'Started from command line' in cause:
            return 'RPM update in enabled repos'
        elif 'Started by user' in cause:
            return 'Manually triggered by admin'
        else:
            return 'Unknown'
    except KeyError:
        return 'Invalid JSON response from Jenkins'


def get_cause_of_build(jenkins_url, job_name, job_number):
    """
    This function expects Jenkins endpoint, job name and job number to figure
    the cause of build
    """
    url = "http://{}:8080/job/{}/{}/api/json".format(
        jenkins_url, job_name, job_number)
    try:
        response = urllib2.urlopen(url)
    except Exception:
        return "Error fetching cause of build from: {}".format(url)
    else:
        return parse_json_response(json.loads(response.read()))


# In future, we can collate a lot of duplicate code from workers
# to manage and track build, thereby providing a clean interface
# to manage builds and prevent duplication of code.
class BuildTracker:
    """Track image build status in the pipeline"""
    def __init__(self, name, datadir='/srv/pipeline-logs', logger=None):
        self.name = name
        self._path = os.path.join(datadir, name)
        self.logger = logger or logging.getLogger('console')

    def is_running(self):
        """Check if pipeline build is running"""
        # We touch a file at self._path when start() is called. This file
        # gets deleted when complete() is called to mark the pipeline
        # build as complete. So, as long as the file self._path exists
        # we identify the build to be running, else, we consider it as
        # not running.
        if os.path.exists(self._path):
            return True
        else:
            return False

    def start(self):
        """Mark build as running"""
        # This touches a file at self._path to say that the current build is
        # running
        with open(self._path, 'a'):
            os.utime(self._path, None)
        self.logger.info('Created lock file for {} at {}'.format(
            self.name, self._path))

    def complete(self):
        """Mark build as complete"""
        # This removes the file at self._path and marks the pipeline build
        # as not running
        if self.is_running():
            os.remove(self._path)
            self.logger.info('Removing lock file for {} at {}'.format(
                self.name, self._path))
