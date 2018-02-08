from datetime import datetime, date
from glob import glob
from os import environ, path, mkdir, unsetenv, listdir, unlink, devnull, getenv
from shutil import rmtree
from subprocess import check_call, CalledProcessError, STDOUT

from yaml import load

from dependency_validation import DependencyValidator
from summary import Summary


def execute_command(cmd):
    """Execute a specified command"""
    try:
        fnull = open(devnull, "w")
        check_call(cmd, stdout=fnull, stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


class Environment(object):
    """Handles the bringing up and teardown of the test environment"""

    def __init__(self):

        home = getenv("HOME")
        if home:
            dump_location = home + "/cccp-index-test"
        else:
            dump_location = "./cccp-index-test"

        if not path.isabs(dump_location):
            dump_location = path.abspath(dump_location)

        self.dump_directory = dump_location
        self.index_test_bench = dump_location + "/index_test_bench"
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%s")
        self.index_dir = self.index_test_bench + "/" + time_stamp
        self.test_index = self.index_dir + "/index.d"
        self.summary_location = self.index_dir + "/summary.log"
        self.repo_dump = dump_location + "/repositories"
        generator_location = dump_location + "_generator_ref/"
        self.generator_dir = generator_location + time_stamp
        self.verbose = False

        self.old_environ = dict(environ)

        # Create all test bench directory structure
        for item in [self.dump_directory, self.index_test_bench, self.index_dir, self.test_index, self.repo_dump,
                     generator_location, self.generator_dir]:
            try:
                if not path.exists(item):
                    mkdir(item)
            except Exception as ex:
                print "Failed to create test bench file structure : " + str(ex)
                exit(1)

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

    def cleanup_index_testbench(self, full=False):
        """Clean up the test bench directory"""
        if full:
            self._cleanup_content(self.index_test_bench)
        else:
            removables = glob(self.index_test_bench + "/*")
            for removable in removables:
                removable_name = path.basename(removable)
                removable_date_str = removable_name.split("_")[0]
                removeable_date = datetime.strptime(removable_date_str, "%Y-%m-%d").date()
                current_date = date.today()
                if removeable_date < current_date:
                    self._cleanup_content(removable)
                    rmtree(removable)

    def teardown(self, cleanup_test_bench=False):
        """Tear down the environment"""
        environ.update(self.old_environ)
        if cleanup_test_bench:
            self._cleanup_content(self.dump_directory)
        else:
            self.cleanup_index_testbench()


class Context(object):
    def __init__(self):
        self.environment = Environment()
        self.summary = Summary(self.environment.summary_location)
        self.dependency_validator = DependencyValidator()


class StatusIterator(object):
    def __init__(self, generator_ref_dir):
        self._current = -1
        self._src = glob(generator_ref_dir + "/*.y*ml")
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

        if not path.exists(self._src):
            raise Exception("The source directory for directory no longer exists")
        with open(self._src[self._current]) as current_file:
            current_file_content = load(current_file)

        return {
            "namespace": self._src[self._current],
            "list": current_file_content
        }
