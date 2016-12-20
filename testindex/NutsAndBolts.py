from glob import glob
from os import environ, path, mkdir, unsetenv, listdir, unlink, devnull, getenv
from shutil import rmtree
from subprocess import check_call, CalledProcessError, STDOUT
from yaml import load


def execute_command(cmd):
    """Execute a specified command"""
    try:
        FNULL = open(devnull, "w")
        check_call(cmd, stdout=FNULL, stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


class Environment(object):
    """Handles the bringing up and teardown of the test environment"""

    def __init__(self, data_dump_directory="./cccp-index-test"):

        if not path.isabs(data_dump_directory):
            data_dump_directory = path.abspath(data_dump_directory)

        self.data_dump_directory = data_dump_directory
        self.indexd_test_bench = data_dump_directory + "/index_d"
        self.repo_dump = data_dump_directory + "/repos"
        self.generator_dir = getenv("HOME") + "/generator_ref"

        self.old_environ = dict(environ)

        if not path.exists(self.data_dump_directory):
            mkdir(data_dump_directory)

        if not path.exists(self.indexd_test_bench):
            mkdir(self.indexd_test_bench)

        if not path.exists(self.repo_dump):
            mkdir(self.repo_dump)

        if not path.exists(self.generator_dir):
            mkdir(self.generator_dir)

        if path.exists(self.generator_dir):
            self._cleanup_content(self.generator_dir)

        if not path.exists(self.generator_dir):
            mkdir(self.generator_dir)

        unsetenv("GIT_ASKPASS")
        unsetenv("SSH_ASKPASS")

    @staticmethod
    def _cleanup_content(folder, del_sub_dirs=True):
        """Wipes a directoy clean without deleting the directory"""
        for current_file in listdir(folder):

            file_path = path.join(folder, current_file)

            try:
                if path.isfile(file_path):
                    unlink(file_path)

                elif del_sub_dirs and path.isdir(file_path):
                    rmtree(file_path)

            except Exception as e:
                print e

    def cleanup_index_testbench(self):
        """Clean up the test bench directory"""
        self._cleanup_content(self.indexd_test_bench)

    def teardown(self, cleanup_test_bench=False):
        """Tear down the environment"""
        environ.update(self.old_environ)
        if cleanup_test_bench:
            self._cleanup_content(self.data_dump_directory)


class GlobalEnvironment:
    environment = None


class StatusIterator:
    def __init__(self):
        self._current = -1
        self._src = glob(GlobalEnvironment.environment.generator_dir + "/*.yml")
        self._src_count = len(self._src)

    def __iter__(self):
        return self

    def __next__(self):
        return self

    def reset(self):
        self._current = -1

    def next(self):
        self._current += 1

        if self._current >= self._src_count:
            raise StopIteration

        with open(self._src[self._current]) as current_file:
            current_file_content = load(current_file)

        return {
            "namespace": self._src[self._current],
            "list": current_file_content
        }
