from glob import glob
from os import path

from sys import exit
from yaml import dump

import Validators
from NutsAndBolts import Environment, GlobalEnvironment, StatusIterator
from Summary import Summary


class Engine:
    def __init__(self, index_location="./index.d", dump_location="cccp-index-test", cleanup=False):

        self._success = False
        self._cleanup = cleanup

        print "\nSetting up environment...\n"
        GlobalEnvironment.environment = Environment(dump_location)

        print "\nChecking index directory\n"

        self._prepare_index_test_bench(index_location)

    @staticmethod
    def _prepare_index_test_bench(indexd_location):
        """Copies the indexd files into testbench so we can modify if needed without affecting originals"""

        if not path.exists(indexd_location):
            print ("\nInvalid index location specified.\n")
            exit(1)

        if not path.isdir(indexd_location):
            print "\nThe path specified must be a directory\n"
            exit(1)

        print "\nPreparing the test bench from the index files\n"
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
        status_list = list()

        print "Processing the data, please wait a while...\n"

        for index_path in glob(GlobalEnvironment.environment.indexd_test_bench + "/*.yml"):
            index_file = path.basename(index_path)

            status1, status_sublist1 = Validators.IndexFormatValidator(index_path).run()

            if status1:

                status2, status_sublist2 = Validators.IndexProjectsValidator(index_path).run()

                if status2:
                    flags_list.append(True)
                    Validators.DependencyValidationUpdater(index_path).run()

                else:
                    flags_list.append(False)

                with open(GlobalEnvironment.environment.generator_dir + "/" + index_file, "w+") as the_file:
                    dump(status_sublist2, the_file)
                status_list.append(index_file)

            else:
                flags_list.append(False)

            if index_file not in status_list:
                status_list.append(index_file)
                with open(GlobalEnvironment.environment.generator_dir + "/" + index_file, "w+") as the_file:
                    dump(status_sublist1, the_file)

        Summary.print_summary()

        GlobalEnvironment.environment.teardown(self._cleanup)
        status = StatusIterator()

        if False in flags_list:
            return False, status, None

        dep_status = Validators.DependencyValidator.is_dependency_acyclic()
        dep_graph = Validators.DependencyValidator.dependency_graph

        print str.format("Dependency Graph : \n\nContainers: \n{}\n\nDependencies : \n{}\n",
                         dep_graph.get_internal_graph().nodes(data=True), dep_graph.get_internal_graph().edges())

        if not dep_status:
            print "DEPENDENCY ERROR : "
            print str.format("The dependencies among the containers is found to be cyclic, please resolve the same\n"
                             "Cycles Found : \n{}", dep_graph.get_cycles())

        return dep_status, status, Validators.DependencyValidator.dependency_graph

    def run_light(self):
        """Does a light run, DO NOT run the normal run, if you use this"""

        success_list = []
        success = True
        print "Processing the data, please wait a while...\n"
        for index_path in glob(GlobalEnvironment.environment.indexd_test_bench + "/*.yml"):
            success_list.append(Validators.LightWeightValidator(index_path).run())

        if False in success_list:
            success = False

        Summary.print_summary()
        GlobalEnvironment.environment.teardown(cleanup_test_bench=True)
        return success, Validators.DependencyValidator.dependency_graph
