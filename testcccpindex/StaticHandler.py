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
    def markcustomindexusage():

        with open(ValidatorGlobals.customindexused, "a+"):
            os.utime(ValidatorGlobals.customindexused, None)

        return

    @staticmethod
    def unmarkcustomindexusage():

        if os.path.exists(ValidatorGlobals.customindexused):
            os.remove(ValidatorGlobals.customindexused)

        return

    @staticmethod
    def customindexused():

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

        clonesuccess = False

        if clone:
            # If need to clone, then clone repo and store status in flag.

            StaticHandler.print_msg(MessageType.info, "Cloning index repo...")
            # Clone the index repo
            cmd = ["git", "clone", ValidatorGlobals.indexgit, ValidatorGlobals.testdir + "/index"]

            clonesuccess = StaticHandler.execcmd(cmd)

        if (not clone) or (clone and clonesuccess):

            StaticHandler.print_msg(MessageType.info, "Updating index repo...")
            currdir = os.getcwd()

            os.chdir(ValidatorGlobals.testdir + "/index")
            cmd = ["git", "fetch", "--all"]
            StaticHandler.execcmd(cmd)

            os.chdir(currdir)

        if clone and not clonesuccess:

            StaticHandler.print_msg(MessageType.error, "Failed to clone index git repo.")

        return

    @staticmethod
    def initialize_all(customindex=False, customindexfile=False):

        # If the test dir does not exist, create it with all permissions
        if not os.path.exists(ValidatorGlobals.testdir):
            os.mkdir(ValidatorGlobals.testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        if customindex:
            # Check if custom index is being used and mark its usage.
            StaticHandler.markcustomindexusage()

            if os.path.exists(ValidatorGlobals.testdir + "/index"):
                shutil.rmtree(ValidatorGlobals.testdir + "/index")

            os.mkdir(ValidatorGlobals.testdir + "/index")

            if customindexfile:
                # If custom index file, copy it over and use it.
                if os.path.exists(ValidatorGlobals.indxfile):

                    if not os.path.isabs(ValidatorGlobals.indxfile):

                        ValidatorGlobals.indxfile = os.path.abspath(ValidatorGlobals.indxfile)

                    StaticHandler.print_msg(MessageType.info, "Copying index to dump location.")

                    shutil.copy2(ValidatorGlobals.indxfile, ValidatorGlobals.testdir + "/index" + "/index.yml")
                    ValidatorGlobals.indxfile = ValidatorGlobals.testdir + "/index" + "/index.yml"

                else:

                    StaticHandler.print_msg(MessageType.error, "The index file you specified, does not exist.")
                    sys.exit(10)

            else:
                # If not custom index file, then its custom index git, clone it in preparation for use.
                StaticHandler.updateIndex(clone=True)

        else:
            # Use default inbuilt giturl

            # Check if custom index has been used, in which case, we will need to reset and clone default giturl

            if StaticHandler.customindexused():

                shutil.rmtree(ValidatorGlobals.testdir + "/index")
                StaticHandler.updateIndex(clone=True)
                StaticHandler.unmarkcustomindexusage()

            else:

                if os.path.exists(ValidatorGlobals.testdir + "/index"):

                    StaticHandler.updateIndex(clone=False)

                else:

                    StaticHandler.updateIndex(clone=True)

        sleep(5)

        ValidatorGlobals.indxfile = ValidatorGlobals.testdir + "/index" + "/index.yml"

        StaticHandler.print_msg(MessageType.info, "Verifying index formatting ...")

        if not IndexVerifier.verify_index():

            StaticHandler.print_msg(MessageType.error, "Index verification failed, getting out.")
            print
            IndexVerifier.print_err_log()
            sys.exit(5)

        IndexVerifier.print_err_log()

        print ValidatorGlobals.indexonly

        if ValidatorGlobals.indexonly:

            sys.exit(0)

        print

        return

    @staticmethod
    def is_valid_git_url(theurl):

        valid = True

        parsedurl = urlparse.urlparse(theurl)
        print parsedurl

        if parsedurl.scheme != "git":

            valid = False

        return valid
