from subprocess import check_call, CalledProcessError, STDOUT
from os import environ, path, mkdir, unsetenv, listdir, unlink, devnull
from shutil import rmtree


def execute_command(cmd):
    """Execute a specified command"""
    try:
        FNULL = open(devnull, "w")
        check_call(cmd, stdout=FNULL, stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


class Environment:
    """Handles the bringing up and teardown of the test environment"""
    def __init__(self, data_dump_directory="./cccp-index-test"):

        if not path.isabs(data_dump_directory):
            data_dump_directory = path.abspath(data_dump_directory)

        self.data_dump_directory = data_dump_directory
        self.indexd_test_bench = data_dump_directory + "/index_d"
        self.repo_dump = data_dump_directory + "/repos"

        self.old_environ = dict(environ)

        if not path.exists(self.data_dump_directory):
            mkdir(data_dump_directory)

        if not path.exists(self.indexd_test_bench):
            mkdir(self.indexd_test_bench)

        if not path.exists(self.repo_dump):
            mkdir(self.repo_dump)

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

    def teardown(self):
        """Tear down the environment"""
        environ.update(self.old_environ)


class GlobalEnvironment:
    environment = None