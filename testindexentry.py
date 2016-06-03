#!/bin/python
import os
import sys
import yaml
from subprocess import check_call, CalledProcessError, call
import stat
from pprint import PrettyPrinter
from collections import OrderedDict

pp = PrettyPrinter(indent=4)


def setup_yaml():
    """ http://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
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
    def print_msg(messagetype, msg, testentry=None):
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

        if testentry is not None:
            testentry.write_info(pre_fmsg + msg)

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


class TestConsts:
    """Contains constants being used by the script"""

    def __init__(self):

        return

    # This path can be modified by user and it is where the test data will be stored
    # This includes the index file, the repos and test logs
    testdir = os.path.abspath("./cccp-index-test")

    giveexitcode = False
    exitcode = 0

    cmdoptions = {
        "ErrorCode": [
            "-e",
            "--useerrorcode"
        ],
        "IndexEntry": [
            "-i",
            "--indexentry"
        ],
        "Test": [
            "-t",
            "--testentry"
        ],
        "Help": [
            "-h",
            "--help"
        ]
    }

    # If using a local index, just change the path here tpo match that of your index file
    indxfile = testdir + "/index" + "/index.yml"

    # If the test dir does not exist, create it with all permissions
    if not os.path.exists(testdir):
        os.mkdir(testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    # Check if the index repo exists, if it does, fetch the updates.
    if os.path.exists(testdir + "/index"):
        StaticHandler.print_msg(MessageType.info, "Updating index repo...")
        currdir = os.getcwd()
        os.chdir(testdir + "/index")
        cmd = ["git", "fetch", "--all"]
        os.chdir(currdir)

    # If not, clone it
    else:
        StaticHandler.print_msg(MessageType.info, "Cloning index repo...")
        # Clone the index repo
        cmd = ["git", "clone", "https://github.com/kbsingh/cccp-index.git", testdir + "/index"]
        call(cmd)

    print


class TestEntry:
    """This class runs tests on a single entry"""

    def __init__(self, tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail):

        if not gitpath.startswith("/"):
            gitpath = "/" + gitpath

        if not gitpath.endswith("/"):
            gitpath += "/"

        fnm = tid + "_" + appid + "_" + jobid
        self._test_location = TestConsts.testdir + "/repos"

        if not os.path.exists(TestConsts.testdir + "/tests"):
            os.mkdir(TestConsts.testdir + "/tests")

        self.testinfo = TestConsts.testdir + "/tests/" + fnm + ".info"

        self._id = tid
        self._appid = appid
        self._jobid = jobid
        self._giturl = giturl
        self._gitpath = gitpath
        self._gitBranch = gitbranch
        self._notifyEmail = notifyemail

        t = ""

        # The repos will be cloned into this location
        t = self._giturl.split(":")[1]
        if t.startswith("//"):
            t = t[2:]

        self._git_Data_Location = self._test_location + "/" + t

        # The location in the git repo against which the tests are to be run
        self._cccp_test_dir = self._git_Data_Location + self._gitpath

        self._testData = {
            "clone-path": self._git_Data_Location,
            "git-path": self._gitpath,
            "tests": {
                "clone": False,
                "cccpexists": False,
                "jobidmatch": False,
                "test-skip": False,
                "test-script": False,
                "allpass": False
            }
        }

        return

    def write_info(self, msg):
        """Allows outsiders to write to this Entries test.info file."""

        with open(self.testinfo, "a") as infofile:
            infofile.write("\n" + msg + "\n")

        return

    def _init_entries(self):
        """Write the initial entries into this tests log file."""

        info = str.format("ID : {0}\nAPP ID : {1}\nJOB ID : {2}\n", self._id, self._appid, self._jobid)
        print info
        info += "GIT : " + self._giturl + "\n"

        info += "######################################################################################################"
        info += "\n"

        with open(self.testinfo, "w") as infofile:
            infofile.write(info)

        return

    def _update_branch(self):
        """Fetches any changes and checks out specified branch"""

        currdir = os.getcwd()

        os.chdir(self._git_Data_Location)

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

        if os.path.exists(self._git_Data_Location):

            StaticHandler.print_msg(MessageType.info, "Git repo already exist, checking for updates...", self)
            self._update_branch()
            StaticHandler.print_msg(MessageType.success, "Changes if any, have been merged...", self)

        else:

            StaticHandler.print_msg(MessageType.info, "Attempting to clone repo...", self)
            cmd = ["git", "clone", self._giturl, self._git_Data_Location]

            if StaticHandler.execcmd(cmd):
                StaticHandler.print_msg(MessageType.success, "Cloning successful.")
                StaticHandler.print_msg(MessageType.info, "Checking out branch " + self._gitBranch + "...", self)
                self._update_branch()

            else:

                StaticHandler.print_msg(MessageType.error, "Failed to clone repo, skipping...")
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

            if self._jobid == cccpyaml["job-id"]:

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

                        StaticHandler.print_msg(MessageType.success, "The specified test script exists, moving on...", self)
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

        # * Check Local Delivery

        self._testData["tests"]["allpass"] = self._testData["tests"]["cccpexists"] and self._testData["tests"]["clone"]\
                                             and self._testData["tests"]["jobidmatch"] and \
                                             (self._testData["tests"]["test-skip"] and
                                              self._testData["tests"]["test-script"])

        return

    def run_tests(self):
        """This function runs all the nessasary tests and returns the collected test data."""

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        return self._testData


class Tester:
    """This class reads index file and user input and orchestrates the tests accordingly"""

    def __init__(self):
        self._i = ""
        return

    def run(self, args):
        """Runs the tests of the tester."""

        t = self._i

        resultset = {
            "Projects": []
        }

        # Checks if the index file exists. Required for any tests to proceed
        if os.path.exists(TestConsts.indxfile):

            # read in data from index file.
            with open(TestConsts.indxfile) as indexfile:
                indexentries = yaml.load(indexfile)

                i = 0

            # If the args used to run this script contain no args or only one arg, that too requesting errorcode
            if len(args) <= 1 or (len(args) == 2 and args[1] in TestConsts.cmdoptions["ErrorCode"]):

                if len(args) == 2:

                    TestConsts.giveexitcode = True  # Set the flag for error code

                # Assuming no specifics, read all entries in index file and run tests agains them.
                for item in indexentries["Projects"]:

                    if i > 0:

                        testresults = TestEntry(item["id"], item["app-id"], item["job-id"], item["git-url"], item["git-path"],
                                       item["git-branch"], item["notify-email"]).run_tests()

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

            # This assumes more than 2 parameters were passed.
            else:

                # Extract params
                prms = args[1:]
                i = 0

                # read the params
                while i < len(prms):

                    prm = prms[i]

                    # If param specifies fpr index entry, read data adn run tests against the specified project from
                    # index file
                    if prm in TestConsts.cmdoptions["IndexEntry"]:

                        tid = prms[i+1]
                        appid = prms[i+2]
                        jobid = prms[i+3]

                        tid = tid.lstrip()
                        tid = tid.rstrip()

                        appid = appid.lstrip()
                        appid = appid.rstrip()

                        jobid = jobid.lstrip()
                        jobid = jobid.rstrip()

                        t = 0

                        for item in indexentries["Projects"]:

                            if t > 0 and tid == item["id"] and appid == item["app-id"] and jobid == item["job-id"]:

                                testresults = TestEntry(item["id"], item["app-id"], item["job-id"], item["git-url"],
                                               item["git-path"], item["git-branch"], item["notify-email"]).run_tests()


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
                                            "test-summary", testresults["tests"]
                                        ),
                                        (
                                            "git-clone-path", testresults["clone-path"]
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

                            t += 1

                        i += 4

                    # If error code was requested, set the flag
                    elif prm in TestConsts.cmdoptions["ErrorCode"]:

                        TestConsts.giveexitcode = True
                        i += 1

                    # If a test entry was requested, take in all params and run tests against it
                    elif prm in TestConsts.cmdoptions["Test"]:

                        tid = prms[i+1]
                        appid = prms[i+2]
                        jobid = prms[i+3]
                        giturl = prms[i+4]
                        gitpath = prms[i+5]
                        gitbranch = prms[i+6]
                        notifyemail = prms[i+7]

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

                        i += 8

                    # If help was requsted, give help
                    elif prm in TestConsts.cmdoptions["Help"]:

                        print
                        print str.format("Usage : {0} [(--indexproject|-i)|(--testproject|-t)|(--help|-h)] [id appid"
                                         " jobid [giturl gitpath gitbranch notifyemail]]", sys.argv[0])\

                        i += 10000

                    else:

                        i += 1
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
