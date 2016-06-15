#!/bin/python

import argparse
import sys
import os
import yaml
from collections import OrderedDict
from StaticHandler import StaticHandler, MessageType
from TestGlobals import TestGlobals
from TestEntry import TestEntry


class Tester:
    """This class reads index file and user input and orchestrates the tests accordingly"""

    def __init__(self):
        self._i = ""
        self._parser = argparse.ArgumentParser()

        self.init_parser()
        return

    def init_parser(self):

        self._parser = argparse.ArgumentParser(description="This script checks for errors in cccp entries.")
        self._parser.add_argument("-e", "--exitcode", help="The script will use the exit code.", action="store_true")

        self._parser.add_argument("-i",
                                  "--indexentry",
                                  help="Check a specific index entry",
                                  metavar=('ID', 'APPID', 'JOBID'),
                                  nargs=3,
                                  action="append"
                                  )

        self._parser.add_argument("-t",
                                  "--testentry",
                                  help="Check a specified entry without validating against index",
                                  nargs=7,
                                  action="append",
                                  metavar=('ID', 'APPID', 'JOBID', 'GITURL', 'GITPATH', 'GITBRANCH', 'NOTIFYEMAIL')
                                  )

        self._parser.add_argument("-d", "--dumpdirectory", help="Specify your down dump directory, where the test data"
                                                                " including index, repos etc will be dumped",
                                  metavar='DUMPDIRPATH',
                                  nargs=1,
                                  action="store"
                                  )

        self._parser.add_argument("-g",
                                  "--indexgit",
                                  help="Specify a custom git containing the index.yml",
                                  metavar='GITURL',
                                  nargs=1,
                                  action="store"
                                  )

        self._parser.add_argument("-c",
                                  "--customindex",
                                  help="Specify a custom index file, stored locally."
                                       "DO NOT use with -g",
                                  metavar='INDEXPATH',
                                  nargs=1,
                                  action="store"
                                  )

        self._parser.add_argument("-x",
                                  "--indexonly",
                                  help="If this flag is set, only the core index tests are done",
                                  action="store_true"
                                  )

        return

    def run(self):
        """Runs the tests of the tester."""

        t = self._i

        cmdargs = self._parser.parse_args()
        initialized = False

        if cmdargs.indexgit is not None and cmdargs.customindex is not None:
            StaticHandler.print_msg(MessageType.error, "Error, -g and -c are mutually exclusive, specify either one")
            sys.exit(900)

        if cmdargs.indexonly is not None:

            TestGlobals.indexonly = cmdargs.indexonly

        # If dump directory is specified, update the globals
        if cmdargs.dumpdirectory is not None:

            dpth = cmdargs.dumpdirectory[0]

            if not os.path.isabs(dpth):
                dpth = os.path.abspath(dpth)
                TestGlobals.testdir = dpth

            if not os.path.exists(dpth):
                StaticHandler.print_msg(MessageType.error, "Invalid path specified or does not exist")
                sys.exit(900)

        # If index git is specified, update globals
        if cmdargs.indexgit is not None:

            gurl = cmdargs.indexgit[0]
            TestGlobals.indexgit = gurl
            StaticHandler.initialize_all(forceclone=True)
            initialized = True

        # If customindex is specified, initialize appropriately
        if cmdargs.customindex is not None:

            cind = cmdargs.customindex[0]
            TestGlobals.indxfile = cind
            StaticHandler.initialize_all(customindex=True)
            initialized = True

        if not initialized:
            StaticHandler.initialize_all()

        resultset = {
            "Projects": []
        }

        # Checks if the index file exists. Required for any tests to proceed
        if os.path.exists(TestGlobals.indxfile):

            # read in data from index file.
            with open(TestGlobals.indxfile) as indexfile:
                indexentries = yaml.load(indexfile)

                i = 0

            # If exit code is set set the value :
            if cmdargs.exitcode is True:
                TestGlobals.giveexitcode = True

            # If no index entries or test entries were specified do everything
            if cmdargs.indexentry is None and cmdargs.testentry is None:

                # Assuming no specifics, read all entries in index file and run tests agains them.
                for item in indexentries["Projects"]:

                    if i > 0:
                        testresults = TestEntry(item["id"], item["app-id"], item["job-id"], item["git-url"],
                                                item["git-path"], item["git-branch"], item["notify-email"]).run_tests()

                        # Update the result set with the test data.
                        od = OrderedDict(
                            (
                                (
                                    "id", item["id"]
                                ),
                                (
                                    "app-id", item["app-id"]
                                ),
                                (
                                    "job-id", item["job-id"]
                                ),
                                (
                                    "tests-passed", testresults["tests"]["allpass"]
                                ),
                                (
                                    "tests-summary", testresults["tests"]
                                ),
                                (
                                    "git-clone-path", testresults["clone-path"]
                                ),
                                (
                                    "git-track-url", item["git-url"]
                                ),
                                (
                                    "git-path", testresults["git-path"]
                                ),
                                (
                                    "git-branch", item["git-branch"]
                                ),
                                (
                                    "notify-email", item["notify-email"]
                                )
                            )
                        )

                        resultset["Projects"].append(od)

                        print "\nNext Entry....\n"

                    i += 1

            # If indexentries or test entries were passed, parse them
            else:

                if cmdargs.indexentry is not None:

                    for item in cmdargs.indexentry:

                        tid = item[0]
                        appid = item[1]
                        jobid = item[2]

                        tid = tid.lstrip()
                        tid = tid.rstrip()

                        appid = appid.lstrip()
                        appid = appid.rstrip()

                        jobid = jobid.lstrip()
                        jobid = jobid.rstrip()

                        t = 0

                        for item1 in indexentries["Projects"]:

                            if t > 0 and tid == item1["id"] and appid == item1["app-id"] and jobid == item1["job-id"]:

                                testresults = TestEntry(item1["id"], item1["app-id"], item1["job-id"], item1["git-url"],
                                                        item1["git-path"], item1["git-branch"],
                                                        item1["notify-email"]).run_tests()

                                od = OrderedDict(
                                    (
                                        (
                                            "id", item1["id"]
                                        ),
                                        (
                                            "app-id", item1["app-id"]
                                        ),
                                        (
                                            "job-id", item1["job-id"]
                                        ),
                                        (
                                            "tests-passed", testresults["tests"]["allpass"]
                                        ),
                                        (
                                            "test-summary", testresults["tests"]
                                        ),
                                        (
                                            "git-clone-path", testresults["clone-path"]
                                        ),
                                        (
                                            "git-track-url", item1["git-url"]
                                        ),
                                        (
                                            "git-path", testresults["git-path"]
                                        ),
                                        (
                                            "git-branch", item1["git-branch"]
                                        ),
                                        (
                                            "notify-email", item1["notify-email"]
                                        )
                                    )
                                )

                                resultset["Projects"].append(od)

                                print "\nNext Entry....\n"

                            t += 1

                if cmdargs.testentry is not None:

                    # If a test entry was requested, take in all params and run tests against it
                    for item in cmdargs.testentry:

                        tid = item[0]
                        appid = item[1]
                        jobid = item[2]
                        giturl = item[3]
                        gitpath = item[4]
                        gitbranch = item[5]
                        notifyemail = item[6]

                        testresults = TestEntry(tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail).run_tests()

                        # Update the result set with result data

                        od = OrderedDict(
                            (
                                (
                                    "id", tid
                                ),
                                (
                                    "app-id", appid
                                ),
                                (
                                    "job-id", jobid
                                ),
                                (
                                    "tests-passed", testresults["tests"]["allpass"]
                                ),
                                (
                                    "test-summary", testresults["tests"]
                                ),
                                (
                                    "git-clone-path", testresults["clone-path"]
                                ),
                                (
                                    "git-track-url", giturl
                                ),
                                (
                                    "git-path", testresults["git-path"]
                                ),
                                (
                                    "git-branch", gitbranch
                                ),
                                (
                                    "notify-email", notifyemail
                                )
                            )
                        )

                        resultset["Projects"].append(od)

        # Return resultset

        return resultset