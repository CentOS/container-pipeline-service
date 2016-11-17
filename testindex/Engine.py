from glob import glob
from os import path

from sys import exit

import Validators
from NutsAndBolts import Environment, GlobalEnvironment
from Summary import Summary


class Engine:
    def __init__(self, indexd_location="./index.d", data_dump_directory="cccp-index-test", cleanup=False):

        self._success = False
        self._cleanup = cleanup

        print "\nSetting up environment...\n"
        GlobalEnvironment.environment = Environment(data_dump_directory)

        print "\nChecking indexd directory\n"

        self._prepare_index_test_bench(indexd_location)

    @staticmethod
    def _prepare_index_test_bench(indexd_location):
        """Copies the indexd files into testbench so we can modify if needed without affecting originals"""

        if not path.exists(indexd_location):
            print ("\nInvalid indexd location specified.\n")
            exit(1)

        if not path.isdir(indexd_location):
            print "\nThe path specified must be a directory\n"
            exit(1)

        print "\nPreparing the test bench from the index.d files\n"
        potential_files = glob(indexd_location + "/*.yml")

        if len(potential_files) == 0 or (len(potential_files) == 1 and "index_template.yml" in potential_files):
            print "\nThe index.d format directory does not contain potential index files, exiting...\n"
            exit(1)

        GlobalEnvironment.environment.cleanup_index_testbench()

        for item in potential_files:
            if "index_template" not in item:
                if "/" in item:
                    file_name = path.split(item)[1]

                else:
                    file_name = item

                target_file = open(GlobalEnvironment.environment.indexd_test_bench + "/" + file_name, "w")
                # target_file.write("Projects:\n")
                target_file.write(open(item, "r").read())

    def run(self):

        flags_list = []
        status_list = dict()

        print "Processing the data, please wait a while...\n"

        for index_path in glob(GlobalEnvironment.environment.indexd_test_bench + "/*.yml"):
            index_file = path.basename(index_path)

            status1, status_sublist1 = Validators.IndexFormatValidator(index_path).run()

            if status1:

                status2, status_sublist2 = Validators.IndexProjectsValidator(index_path).run()

                if status2:
                    flags_list.append(True)

                else:
                    flags_list.append(False)

                status_list[index_file] = status_sublist2

            else:
                flags_list.append(False)

            if index_file not in status_list:
                status_list[index_file] = status_sublist1

        Summary.print_summary()

        GlobalEnvironment.environment.teardown(self._cleanup)

        if False in flags_list:
            return False, status_list

        return True, None
