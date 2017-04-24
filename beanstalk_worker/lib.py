import os


def get_job_name(job_details):
    """Get jenkins job name from job_detials"""
    return str(job_details['appid']) + "-" + str(job_details['jobid']) + "-" \
        + str(job_details['desired_tag'])


class Build:
    """
    Track image build status in the pipeline

    In future, we can collate a lot of duplicate code from workers
    to manage and track build, thereby providing a clean interface
    to manage builds and prevent duplication of code.
    """

    def __init__(self, name, datadir='/srv/pipeline-logs'):
        self.name = name
        self._path = os.path.join(datadir, name)

    def is_running(self):
        if os.path.exists(self._path):
            return True
        else:
            return False

    def start(self):
        """Mark build as running"""
        f = open(self._path, 'a')
        os.utime(self._path, None)
        f.close()

    def complete(self):
        """Mark build as complete"""
        if self.is_running():
            os.remove(self._path)
