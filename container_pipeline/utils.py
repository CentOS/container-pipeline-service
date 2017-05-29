import os


def get_job_name(job_details):
    """Get jenkins job name from job_detials"""
    return str(job_details['appid']) + "-" + str(job_details['jobid']) + "-" \
        + str(job_details['desired_tag'])


def get_project_name(job):
    """Get project name from job data"""
    return '{}-{}-{}'.format(job['appid'], job['jobid'], job['desired_tag'])


# In future, we can collate a lot of duplicate code from workers
# to manage and track build, thereby providing a clean interface
# to manage builds and prevent duplication of code.
class Build:
    """Track image build status in the pipeline"""
    def __init__(self, name, datadir='/srv/pipeline-logs'):
        self.name = name
        self._path = os.path.join(datadir, name)

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

    def complete(self):
        """Mark build as complete"""
        # This removes the file at self._path and marks the pipeline build
        # as not running
        if self.is_running():
            os.remove(self._path)
