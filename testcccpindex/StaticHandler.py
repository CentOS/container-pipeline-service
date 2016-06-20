#! /bin/bash


import os
from subprocess import check_call, CalledProcessError
import stat
import shutil
import sys
from time import sleep
from IndexVerifier import IndexVerifier
from ValidatorGlobals import ValidatorGlobals
import urlparse


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
    def setIndexGit(url):

        with open(ValidatorGlobals.indexgitfile, "w") as f:
            f.write(url)

        return

    @staticmethod
    def getIndexGit():

        if not os.path.exists(ValidatorGlobals.indexgitfile):
            StaticHandler.setIndexGit("_none_")

        with open(ValidatorGlobals.indexgitfile, "r") as f:
            data = f.readline()

        return data

    @staticmethod
    def markcustomindexfileusage():

        with open(ValidatorGlobals.customindexused, "a+"):
            os.utime(ValidatorGlobals.customindexused, None)

        return

    @staticmethod
    def unmarkcustomindexfileusage():

        if os.path.exists(ValidatorGlobals.customindexused):
            os.remove(ValidatorGlobals.customindexused)

        return

    @staticmethod
    def customindexfileused():

        used = False

        if os.path.exists(ValidatorGlobals.customindexused):

            used = True

        return used

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
    def updateIndex(clone=False):

        success = True

        if clone:

            StaticHandler.print_msg(MessageType.info, "Cloning index repo...")

            if os.path.exists(ValidatorGlobals.testdir + "/index"):

                shutil.rmtree(ValidatorGlobals.testdir + "/index")

            cmd = ["git", "clone", ValidatorGlobals.indexgit, ValidatorGlobals.testdir + "/index"]

            success = StaticHandler.execcmd(cmd)

        if success:

            StaticHandler.print_msg(MessageType.info, "Updated index repo...")
            retpath = os.getcwd()
            os.chdir(ValidatorGlobals.testdir + "/index")

            cmd = ["git", "fetch", "--all"]

            StaticHandler.execcmd(cmd)

            os.chdir(retpath)

        return success

    @staticmethod
    def initialize_all(customindexfile=False):

        # If the test dir does not exist, create it with all permissions
        if not os.path.exists(ValidatorGlobals.testdir):
            os.mkdir(ValidatorGlobals.testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        if customindexfile:
            # Check if custom index is being used and mark its usage.
            StaticHandler.markcustomindexfileusage()
            StaticHandler.print_msg(MessageType.info, "Attempting to copy custom index file over...")

            if os.path.exists(ValidatorGlobals.testdir + "/index"):
                shutil.rmtree(ValidatorGlobals.testdir + "/index")

            os.mkdir(ValidatorGlobals.testdir + "/index")

            if os.path.exists(ValidatorGlobals.indxfile):

                shutil.copy2(ValidatorGlobals.indxfile, ValidatorGlobals.testdir + "/index/index.yml")

            else:

                StaticHandler.print_msg(MessageType.error, "Invalid Index file specified, getting out...")

        else:

            currgit = StaticHandler.getIndexGit()
            customindexfused = StaticHandler.customindexfileused()
            cloned = False

            if customindexfused:

                StaticHandler.unmarkcustomindexfileusage()
                cloned = StaticHandler.updateIndex(clone=True)

            else:

                if currgit == ValidatorGlobals.indexgit:

                    cloned = StaticHandler.updateIndex(clone=False)

                else:

                    cloned = StaticHandler.updateIndex(clone=True)

            if not cloned:

                StaticHandler.print_msg(MessageType.error, "Index cloning failed, exiting")
                sys.exit(3)

            else:

                StaticHandler.setIndexGit(ValidatorGlobals.indexgit)

        sleep(5)

        ValidatorGlobals.indxfile = ValidatorGlobals.testdir + "/index" + "/index.yml"

        StaticHandler.print_msg(MessageType.info, "Verifying index formatting ...")

        if not IndexVerifier.verify_index():

            StaticHandler.print_msg(MessageType.error, "Index verification failed, getting out.")
            print
            IndexVerifier.print_err_log()
            sys.exit(4)

        IndexVerifier.print_err_log()

        print ValidatorGlobals.indexonly

        if ValidatorGlobals.indexonly:

            sys.exit(0)

        print

        return

    @staticmethod
    def is_valid_git_url(theurl):

        valid = True

        if theurl is None:

            return False

        parsedurl = urlparse.urlparse(theurl)

        if parsedurl.scheme != "git":

            valid = False

        return valid
