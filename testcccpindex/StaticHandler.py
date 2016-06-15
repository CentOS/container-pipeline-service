#! /bin/bash


import os
from subprocess import check_call, CalledProcessError
import stat
import shutil
import sys
from time import sleep
from IndexVerifier import IndexVerifier
from ValidatorGlobals import ValidatorGlobals


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
    def initialize_all(customindex=False, forceclone=False):

        # If the test dir does not exist, create it with all permissions
        if not os.path.exists(ValidatorGlobals.testdir):
            os.mkdir(ValidatorGlobals.testdir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.mkdir(ValidatorGlobals.testdir + "/index")

        if not customindex:
            # Check if the index repo exists, if it does, fetch the updates.
            if not forceclone and os.path.exists(ValidatorGlobals.testdir + "/index/index.yml"):

                StaticHandler.print_msg(MessageType.info, "Updating index repo...")
                currdir = os.getcwd()
                os.chdir(ValidatorGlobals.testdir + "/index")
                cmd = ["git", "fetch", "--all"]
                os.chdir(currdir)

            # If not, clone it
            else:

                if os.path.exists(ValidatorGlobals.testdir + "/index"):

                    shutil.rmtree(ValidatorGlobals.testdir + "/index")

                StaticHandler.print_msg(MessageType.info, "Cloning index repo...")
                # Clone the index repo
                cmd = ["git", "clone", ValidatorGlobals.indexgit, ValidatorGlobals.testdir + "/index"]

                if StaticHandler.execcmd(cmd):

                    currdir = os.getcwd()
                    os.chdir(ValidatorGlobals.testdir + "/index")
                    cmd = ["git", "fetch", "--all"]
                    os.chdir(currdir)

                else:
                    StaticHandler.print_msg(MessageType.error, "Could not clone the git index repo,"
                                                               " please check the url")
                    sys.exit(900)
        else:

            if os.path.exists(ValidatorGlobals.indxfile):

                if not os.path.isabs(ValidatorGlobals.indxfile):

                    ValidatorGlobals.indxfile = os.path.abspath(ValidatorGlobals.indxfile)

                StaticHandler.print_msg(MessageType.info, "Copying index to dump location.")
                shutil.copy2(ValidatorGlobals.indxfile, ValidatorGlobals.testdir + "/index" + "/index.yml")

            else:

                StaticHandler.print_msg(MessageType.error, "The index file you specified, does not exist.")
                sys.exit(900)

            sleep(5)

        ValidatorGlobals.indxfile = ValidatorGlobals.testdir + "/index" + "/index.yml"

        StaticHandler.print_msg(MessageType.info, "Verifying index formatting ...")

        if not IndexVerifier.verify_index():

            StaticHandler.print_msg(MessageType.error, "Index verification failed, getting out.")
            print
            IndexVerifier.print_err_log()
            sys.exit(900)

        print ValidatorGlobals.indexonly

        if ValidatorGlobals.indexonly:

            sys.exit(0)

        print

        return
