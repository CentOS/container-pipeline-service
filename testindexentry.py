#!/bin/python
import os
import stat
import sys
from collections import OrderedDict
from pprint import PrettyPrinter
from subprocess import check_call, CalledProcessError, call
from time import sleep
import argparse

import yaml

pp = PrettyPrinter(indent=4)


def setup_yaml():
    """ http://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)


setup_yaml()


class MessageType:
    def __init__(self):
        return

    error = "1"
    info = "2"
    success = "3"


class StaticHandler:
    def __init__(self):

        return

    @staticmethod
    def print_msg(messagetype, msg, writeinfoobj=None):
        """Prints the status messages of the script onto stdout."""

        pre_pmsg = ""
        pre_fmsg = ""

        if messagetype == MessageType.error:
            pre_pmsg = "\n \033[1;31m[ERROR]\033[0m "
            pre_fmsg = "ERROR\t"

        elif messagetype == MessageType.info:
            pre_pmsg = "\n \033[1;33m[INFO]\033[0m "
            pre_fmsg = "INFO\t"

        elif messagetype == MessageType.success:
            pre_pmsg = "\n \033[1;32m[SUCCESS]\033[0m "
            pre_fmsg = "SUCCESS\t"

        print pre_pmsg + msg
        print

        if writeinfoobj is not None:
            writeinfoobj.write_info(pre_fmsg + msg)

        return

    @staticmethod
    def execcmd(cmd):
        """Executes a cmd list and returns true if cmd executed correctly."""

        success = True

        try:
            check_call(cmd)
            success = True

        except CalledProcessError:
            success = False

        return success

    @staticmethod
    def initialize_all(customindex=False):

        # If the test dir does not exist, create it with all permissions
        if not os.path.exists(TestConsts.testdir):
            os.mkdir(TestConsts.testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        if not customindex:
            # Check if the index repo exists, if it does, fetch the updates.
            if os.path.exists(TestConsts.testdir + "/index"):
                StaticHandler.print_msg(MessageType.info, "Updating index repo...")
                currdir = os.getcwd()
                os.chdir(TestConsts.testdir + "/index")
                cmd = ["git", "fetch", "--all"]
                os.chdir(currdir)

            # If not, clone it
            else:
                StaticHandler.print_msg(MessageType.info, "Cloning index repo...")
                # Clone the index repo
                cmd = ["git", "clone", TestConsts.indexgit, TestConsts.testdir + "/index"]
                call(cmd)
                currdir = os.getcwd()
                os.chdir(TestConsts.testdir + "/index")
                cmd = ["git", "fetch", "--all"]
                os.chdir(currdir)
                sleep(5)

        TestConsts.indxfile = TestConsts.testdir + "/index" + "/index.yml"

        print

        return


class TestConsts:
    """Contains constants being used by the script"""

    def __init__(self):

        return

    # This path can be modified by user and it is where the test data will be stored
    # This includes the index file, the repos and test logs
    testdir = os.path.abspath("./cccp-index-test")

    giveexitcode = False
    exitcode = 0

    # If using a local index, just change the path here tpo match that of your index file
    indxfile = testdir + "/index" + "/index.yml"

    # If need to alter the giturl, edit this
    indexgit = "https://github.com/kbsingh/cccp-index.git"



class TestEntry:
    """This class runs tests on a single entry"""

    def __init__(self, tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail):

        if not gitpath.startswith("/"):
            gitpath = "/" + gitpath

        if not gitpath.endswith("/"):
            gitpath += "/"

        fnm = tid + "_" + appid + "_" + jobid
        self._gitReposlocation = TestConsts.testdir + "/repos"

        if not os.path.exists(TestConsts.testdir + "/tests"):
            os.mkdir(TestConsts.testdir + "/tests")

        self._testLogFile = TestConsts.testdir + "/tests/" + fnm + ".log"

        self._id = tid
        self._appId = appid
        self._jobId = jobid
        self._gitURL = giturl
        self._gitPath = gitpath
        self._gitBranch = gitbranch
        self._notifyEmail = notifyemail

        t = ""

        # The repos will be cloned into this location
        t = self._gitURL.split(":")[1]
        if t.startswith("//"):
            t = t[2:]

        self._gitCloneLocation = self._gitReposlocation + "/" + t

        # The location in the git repo against which the tests are to be run
        self._cccp_test_dir = self._gitCloneLocation + self._gitPath

        self._testData = {
            "clone-path": self._gitCloneLocation,
            "git-path": self._gitPath,
            "tests": {
                "clone": False,
                "cccpexists": False,
                "jobidmatch": False,
                "test-skip": False,
                "test-script": False,
                "build-script": False,
                "allpass": False
            }
        }

        return

    def write_info(self, msg):
        """Allows outsiders to write to this Entries test.info file."""

        with open(self._testLogFile, "a") as infofile:
            infofile.write("\n" + msg + "\n")

        return

    def _init_entries(self):
        """Write the initial entries into this tests log file."""

        info = str.format("ID : {0}\nAPP ID : {1}\nJOB ID : {2}\n", self._id, self._appId, self._jobId)
        print info
        info += "GIT : " + self._gitURL + "\n"

        info += "######################################################################################################"
        info += "\n"

        with open(self._testLogFile, "w") as infofile:
            infofile.write(info)

        return

    def _update_branch(self):
        """Fetches any changes and checks out specified branch"""

        currdir = os.getcwd()

        os.chdir(self._gitCloneLocation)

        cmd = ["git", "branch", self._gitBranch]
        call(cmd) or True

        cmd = ["git", "fetch", "--all"]
        call(cmd)

        cmd = ["git", "checkout", self._gitBranch]
        call(cmd)

        os.chdir(currdir)

        return

    def _clone_repo(self):
        """Function attempts to clone the git repo associated with the entry"""

        success = True

        if os.path.exists(self._gitCloneLocation):

            StaticHandler.print_msg(MessageType.info, "Git repo already exist, checking for updates...", self)
            self._update_branch()
            StaticHandler.print_msg(MessageType.success, "Changes if any, have been merged...", self)

        else:

            StaticHandler.print_msg(MessageType.info, "Attempting to clone repo...", self)
            cmd = ["git", "clone", self._gitURL, self._gitCloneLocation]

            if StaticHandler.execcmd(cmd):
                StaticHandler.print_msg(MessageType.success, "Cloning successful.")
                StaticHandler.print_msg(MessageType.info, "Checking out branch " + self._gitBranch + "...", self)
                self._update_branch()

            else:

                StaticHandler.print_msg(MessageType.error, "Failed to clone repo, skipping...", self)
                TestConsts.exitcode += 1
                success = False

        self._testData["tests"]["clone"] = success
        return success

    def _test_cccp_yaml(self):
        """Run sanity checks on the cccp.yml file"""

        # FIXME : Finish this method

        # * Find out the the cccp yml file is present

        # Map location of the cccp.yml file
        cccpyamlfilepath = ""

        StaticHandler.print_msg(MessageType.info, "Checking if a cccp.yml file exists at specified location", self)

        # Check if the cccp.yml file exists
        pthexists = False
        for itm in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:

            cccpyamlfilepath = self._cccp_test_dir + itm

            if os.path.exists(cccpyamlfilepath):
                pthexists = True
                self._testData["tests"]["cccpexists"] = True
                break

        if not pthexists:
            StaticHandler.print_msg(MessageType.error, "Missing cccp.yml file, skipping...", self)
            return

        StaticHandler.print_msg(MessageType.success, "Found cccp.yml file, moving on...", self)

        # * Validate for job-id

        # Check if the job id supplied matches with job id in cccp.yml
        with open(cccpyamlfilepath) as cccpyamlfile:
            cccpyaml = yaml.load(cccpyamlfile)

        StaticHandler.print_msg(MessageType.info, "Matching job id with one in cccp.yml", self)

        #        print str.format("index jid : {0}\ncccp jid : {1}", self._jobid, cccpyaml["job-id"])

        if "job-id" in cccpyaml.keys():

            if self._jobId == cccpyaml["job-id"]:

                StaticHandler.print_msg(MessageType.success, "Job id matched, moving on...", self)
                self._testData["tests"]["jobidmatch"] = True

            else:

                StaticHandler.print_msg(MessageType.error, "Job Ids don't match, skipping...", self)
                TestConsts.exitcode += 1
                return

        else:

            StaticHandler.print_msg(MessageType.error, "Missing compulsory key, job-id in cccp.yml file...", self)
            TestConsts.exitcode += 1
            return

        # * Validate for test-skip and test-script

        StaticHandler.print_msg(MessageType.info, "Checking for test-skip flag", self)

        # Check for test skip to be present
        if "test-skip" in cccpyaml.keys():

            StaticHandler.print_msg(MessageType.info, "Flag found, proceeding to check if its reset...", self)

            # Check is test-skip is reset
            if cccpyaml["test-skip"] == False:

                StaticHandler.print_msg(MessageType.info, "Test skip is reset, checking for now compulsory test-script",
                                        self)

                self._testData["tests"]["test-skip"] = True

                # Check if a test-script key is present
                if "test-script" in cccpyaml.keys():

                    testscript = cccpyaml["test-script"]
                    testscriptpath = self._cccp_test_dir + testscript

                    # Check if the test script actually exists
                    if not os.path.exists(testscriptpath):

                        StaticHandler.print_msg(MessageType.error,
                                                "The specified test script does not exist, skipping...", self)

                        TestConsts.exitcode += 1
                        return

                    else:

                        StaticHandler.print_msg(MessageType.success, "The specified test script exists, moving on...",
                                                self)

                        self._testData["tests"]["test-script"] = True

                else:

                    StaticHandler.print_msg(MessageType.error,
                                            "Test skip is reset, but test script is missing, skipping...", self)
                    TestConsts.exitcode += 1
                    return

            # If test-skip is not reset, check if its set
            elif cccpyaml["test-skip"] == True:

                StaticHandler.print_msg(MessageType.success, "Test skip is set, moving on...", self)
                self._testData["tests"]["test-skip"] = True
                self._testData["tests"]["test-script"] = True

            # If test-skip is not reset or set, then, there is an error
            else:

                StaticHandler.print_msg(MessageType.error, "Test skip is not reset or set, skipping...", self)
                TestConsts.exitcode += 1
                return

        else:

            StaticHandler.print_msg(MessageType.success, "Test skip not found, assuming True and moving on...", self)
            self._testData["tests"]["test-skip"] = True
            self._testData["tests"]["test-script"] = True

        # * Check Build script
        StaticHandler.print_msg(MessageType.info, "Checking for build script.", self)
        if "build-script" in cccpyaml.keys():

            buildscriptfile = cccpyaml["build-script"]
            buildscriptpath = self._cccp_test_dir + buildscriptfile

            if not os.path.exists(buildscriptpath):

                StaticHandler.print_msg(MessageType.error, "Could not find build script, skipping", self)
                TestConsts.exitcode += 1
                return

            else:
                StaticHandler.print_msg(MessageType.success, "Found specified build script.", self)
                self._testData["tests"]["build-script"] = True

        else:

            StaticHandler.print_msg(MessageType.success, "No build script specified, moving on", self)
            self._testData["tests"]["build-script"] = True

        # * Check Local Delivery

        # * Set the all pass flag
        self._testData["tests"]["allpass"] = self._testData["tests"]["cccpexists"] and self._testData["tests"][
            "clone"] and self._testData["tests"]["jobidmatch"] and \
            (
                self._testData["tests"]["test-skip"] and
                self._testData["tests"]["test-script"]
            ) and\
            self._testData["tests"]["build-script"]

        return

    def run_tests(self):
        """This function runs all the necessary tests and returns the collected test data."""

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        sleep(4)

        return self._testData


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
                                  help="Check a specific index entry", metavar=('ID', 'APPID', 'JOBID'),
                                  nargs=3, action="append")

        self._parser.add_argument("-t", "--testentry", help="Check a specified entry without validating against index",
                                                            nargs=7, action="append",
                                  metavar=('ID', 'APPID', 'JOBID', 'GITURL', 'GITPATH', 'GITBRANCH', 'NOTIFYEMAIL'))

        self._parser.add_argument("-d", "--dumpdirectory", help="Specify your down dump directory, where the test data"
                                                                " including index, repos etc will be dumped",
                                  metavar=('DUMPDIRPATH'), nargs=1, action="store")

        self._parser.add_argument("-g", "--indexgit", help="Specify a custom git containing the index.yml",
                                  metavar=('GITURL'), nargs=1, action="store")

        return

    def run(self, args):
        """Runs the tests of the tester."""

        t = self._i

        cmdargs = self._parser.parse_args()

        if cmdargs.dumpdirectory is not None:

            dpth = cmdargs.dumpdirectory[0]

            if not os.path.isabs(dpth):
                dpth = os.path.abspath(dpth)
                TestConsts.testdir = dpth

            if not os.path.exists(dpth):
                StaticHandler.print_msg(MessageType.error, "Invalid path specified or does not exist")
                sys.exit(900)

        if cmdargs.indexgit is not None:

            gurl = cmdargs.indexgit[0]
            TestConsts.indexgit = gurl

        # FIXME: add entry for
        StaticHandler.initialize_all()

        resultset = {
            "Projects": []
        }

        # Checks if the index file exists. Required for any tests to proceed
        if os.path.exists(TestConsts.indxfile):

            # read in data from index file.
            with open(TestConsts.indxfile) as indexfile:
                indexentries = yaml.load(indexfile)

                i = 0

            # If exit code is set set the value :
            if cmdargs.exitcode is True:
                TestConsts.giveexitcode = True

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


def mainf():
    rs = Tester().run(sys.argv)

    print "\nTests completed\n"
    resultsfile = TestConsts.testdir + "/results.yml"

    with open(resultsfile, "w") as resfile:
        yaml.dump(rs, resfile, default_flow_style=False)

    print "\nYou can view the test results at " + resultsfile + "\n"

    if TestConsts.giveexitcode:
        sys.exit(TestConsts.exitcode)


if __name__ == '__main__':
    mainf()
