from glob import glob
from os import path
from sys import exit

from yaml import dump

import validators
from nuts_and_bolts import Context, StatusIterator, _print


class Engine:
    def __init__(self, index_path="./index_path.d", cleanup=False, verbose=True):
        """
        Initializes the Engine
        Keyword arguments:
            index_path -- The path of the index.d directory
            cleanup -- If true, causes the code to cleanup residue such as repo dirs and so on
            verbose -- If true, will produce process information and summary on stdout
        """

        self._success = False
        self._cleanup = cleanup
        if verbose:
            print("\nSetting up environment...\n")
        self._context = Context()
        self._context.environment.verbose = verbose

        _print(self._context, "\nChecking index  directory\n")

        self._prepare_index_test_bench(index_path)

    def _prepare_index_test_bench(self, index_path):
        """
        Copies the index files into test bench so we can modify if needed without affecting originals
        Keyword arguments:
            index_path -- The path of the index directory
        """

        if not path.exists(index_path):
            _print(self._context, "\nInvalid index path specified.\n")
            exit(1)

        if not path.isdir(index_path):
            _print("\nThe path specified must be a directory\n")
            exit(1)

        _print(self._context, "\nPreparing the test bench from the index files\n")
        potential_files = glob(index_path + "/*.yml")

        if len(potential_files) == 0 or (len(potential_files) == 1 and "index_template.yml" in potential_files):
            _print(self._context, "\nThe index.d format directory does not contain potential index files, exiting...\n")
            exit(1)

        for item in potential_files:
            if "index_template" not in item:
                if "/" in item:
                    file_name = path.split(item)[1]

                else:
                    file_name = item

                target_file = open(self._context.environment.test_index + "/" + file_name, "w")
                target_file.write(open(item, "r").read())

    def run(self):
        """Runs the complete tests and returns 3 parameters ie overall status, individual status iterator and container
         dependency graph"""

        flags_list = []
        status_list = list()

        _print(self._context, "Processing the data, please wait a while...\n")

        for index_path in glob(self._context.environment.test_index + "/*.yml"):
            index_file = path.basename(index_path)

            status1, status_sublist1 = validators.IndexFormatValidator(self._context, index_path).run()

            if status1:

                status2, status_sublist2 = validators.IndexProjectsValidator(self._context, index_path).run()

                if status2:
                    flags_list.append(True)
                    validators.DependencyValidationUpdater(self._context, index_path).run()

                else:
                    flags_list.append(False)

                with open(self._context.environment.generator_dir + "/" + index_file, "w+") as the_file:
                    dump(status_sublist2, the_file)
                status_list.append(index_file)

            else:
                flags_list.append(False)

            if index_file not in status_list:
                status_list.append(index_file)
                with open(self._context.environment.generator_dir + "/" + index_file, "w+") as the_file:
                    dump(status_sublist1, the_file)

        if self._context.environment.verbose:
            self._context.summary.print_summary()

        status = StatusIterator(self._context.environment.generator_dir)

        if False in flags_list:
            return False, status, None

        dep_status = self._context.dependency_validator.is_dependency_acyclic()
        dep_graph = self._context.dependency_validator.dependency_graph

        if self._context.environment.verbose:
            print("Dependency Graph : \n\n* Containers : \n")
            dep_graph.print_node_info(["from_index", "from_target_file", "name"])
            print("\n* Dependencies : \n")
            dep_graph.print_edge_info()
            print("")

        if not dep_status and self._context.environment.verbose:
            print("** Dependency Error : ")
            print(str.format("The dependencies among the containers is found to be cyclic, please resolve the same\n"
                             "Cycles Found : \n{}", dep_graph.get_cycles()))

        self._context.environment.teardown(self._cleanup)
        return dep_status, status, self._context.dependency_validator.dependency_graph

    def run_light(self):
        """Does a lighter run, running only few compulsory tests. DO NOT run the normal run, if you use this
        Returns status flag and the container dependency graph object"""

        success_list = []
        success = True
        _print(self._context, "Processing the data, please wait a while...\n")
        for index_path in glob(self._context.environment.indexd_test_bench + "/*.yml"):
            success_list.append(validators.LightWeightValidator(self._context, index_path).run())

        if False in success_list:
            success = False
        if not self._context.environment.silent:
            self._context.summary.print_summary()
        self._context.environment.teardown(cleanup_test_bench=True)
        return success, self._context.dependency_validator.dependency_graph