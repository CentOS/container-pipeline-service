#!/bin/python
import os
import sys
import yaml
from subprocess import check_call, CalledProcessError, call
import stat
import shutil
import re

class MessageType:
    error = 1
    info = 2
    success = 3


class StaticHandler:

    @staticmethod
    def print_msg(messagetype, msg, testentry=None):

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

        success = True

        try:
            check_call(cmd)
            success = True

        except CalledProcessError:
            success = False

        return success

class TestConsts:
    testdir = os.path.abspath("./cccp-index-test")

    # If using a local index, just change the path here tpo match that of your index file
    indxfile = testdir + "/index" + "/index.yml"

    if not os.path.exists(testdir):
        os.mkdir(testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    if os.path.exists(testdir + "/index"):
        currdir = os.path.abspath(".")
        os.chdir(testdir + "/index")
        cmd = ["git", "merge", "--all"]
        os.chdir(currdir)

    else:
        StaticHandler.print_msg(MessageType.info,"Cloning index repo...")
        # Clone the index repo
        cmd = ["git", "clone", "https://github.com/kbsingh/cccp-index.git", testdir + "/index"]
        call(cmd)

    print

class TestEntry:

    def __init__(self, tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail):

        if not gitpath.startswith("/"):
            gitpath = "/" + gitpath

        fnm = tid + "_" + appid + "_" + jobid
        self._test_location = TestConsts.testdir + "/repos"

        if not os.path.exists(TestConsts.testdir + "/index-tests"):
            os.mkdir(TestConsts.testdir + "/index-tests")

        self.testinfo = TestConsts.testdir + "/index-tests/" + fnm + ".info"

        self._id = tid
        self._appid = appid
        self._jobid = jobid
        self._giturl = giturl
        self._gitpath = gitpath
        self._gitBranch = gitbranch
        self._notifyEmail = notifyemail
        self._git_Data_Location = self._test_location + "/" + self._giturl
        self._cccp_test_dir = self._git_Data_Location + self._gitpath

        if not self._cccp_test_dir.endswith("/"):
            self._cccp_test_dir += "/"

        return

    def write_info(self, msg):
        """Allows outsiders to write to this Entries test.info file."""

        with open(self.testinfo, "a") as infofile:
            infofile.write("\n" + msg + "\n")

        return

    def _init_entries(self):

        info = str.format("ID : {0}\nAPP ID : {1}\nJOB ID : {2}\n", self._id, self._appid, self._jobid)
        print info
        info += "GIT : " + self._giturl + "\n"

        info += "######################################################################################################"
        info += "\n"

        with open(self.testinfo, "w") as infofile:
            infofile.write(info)

        return

    def _update_branch(self):

        currdir = os.path.abspath(".")

        os.chdir(self._git_Data_Location)

        cmd = ["git", "branch", self._gitBranch]
        call(cmd) or True

        cmd = ["git", "fetch", "--all"]
        call(cmd)

        cmd = ["git", "checkout", self._gitBranch]

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
                success = False

        return success

    def _test_cccp_yaml(self):
        """Run sanity checks on the cccp.yml file"""

        # FIXME : Finish this method

        # Map location of the cccp.yml file
        cccpyamlfilepath = ""

        StaticHandler.print_msg(MessageType.info, "Checking if a cccp.yml file exists at specified location", self)

        # Check if the cccp.yml file exists
        pthexists = False
        for itm in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:

            cccpyamlfilepath = self._cccp_test_dir + itm

            if os.path.exists(cccpyamlfilepath):
                pthexists = True
                break

        if not pthexists:
            StaticHandler.print_msg(MessageType.error, "Missing cccp.yml file, skipping...", self)
            return

        StaticHandler.print_msg(MessageType.success, "Found cccp.yml file", self)

        # Check if the job id supplied matches with job id in cccp.yml
        with open(cccpyamlfilepath) as cccpyamlfile:
            cccpyaml = yaml.load(cccpyamlfile)

        StaticHandler.print_msg(MessageType.info, "Matching job id with one in cccp.yml", self)

#        print str.format("index jid : {0}\ncccp jid : {1}", self._jobid, cccpyaml["job-id"])

        if self._jobid == cccpyaml["job-id"]:

            StaticHandler.print_msg(MessageType.success, "Job id matched, continuing...", self)

        else:

            StaticHandler.print_msg(MessageType.error, "Job Ids dont match, skipping...", self)
            return



        return

    def run_tests(self):

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        return

class Tester:

    def __init__(self):

        return

    def run(self):

        if os.path.exists(TestConsts.indxfile):

            with open(TestConsts.indxfile) as indexfile:
                indexentries = yaml.load(indexfile)

                i = 0

            if len(sys.argv) <= 1:
                for item in indexentries["Projects"]:

                    if i > 0:

                        TestEntry(item["id"], item["app-id"], item["job-id"], item["git-url"], item["git-path"], item["git-branch"], item["notify-email"]).run_tests()
                        print "\nNext Entry....\n"

                    i += 1

            else:

                # Extract params
                prms = sys.argv[1:]

                i = 0

                while i < len(prms):

                    prm = prms[i]

                    if prm == "--indexproject" or prm == "-i":

                        tid = prms[i+1]
                        appid = prms[i+2]
                        jobid = prms[i+3]

                        t = 0

                        for item in indexentries["Projects"]:

                            if t > 0 and tid == item["id"] and appid == item["app-id"] and jobid == item["job-id"]:

                                TestEntry(item["id"], item["app-id"], item["job-id"], item["git-url"], item["git-path"], item["git-branch"], item["notify-email"]).run_tests()
                                print "\nNext Entry....\n"

                            t += 1

                        i += 4

                    elif prm == "--testproject" or prm == "-t":

                        tid = prms[i+1]
                        appid = prms[i+2]
                        jobid = prms[i+3]
                        giturl = prms[i+4]
                        gitpath = prms[i+5]
                        gitbranch = prms[i+6]
                        notifyemail = prms[i+7]

                        TestEntry(tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail).run_tests()

                        i += 8

                    elif prm == "--help" or prm == "-h":

                        print
                        print str.format("Usage : {0} [(--indexproject|-i)|(--testproject|-t)|(--help|-h)] [id appid jobid [giturl gitpath gitbranch notifyemail]]", sys.argv[0])\

                        i += 10000

                    else:

                        i += 1

        return


def mainf():

    Tester().run()

    print "\nTests completed\n"
    print "You can view the test results at " + TestConsts.testdir + "/" + "[id]_[appid]_[jobid]/test.info\n"

if __name__ == '__main__':
    mainf()