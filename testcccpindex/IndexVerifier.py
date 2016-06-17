#!/bin/python

import yaml
from ValidatorGlobals import ValidatorGlobals
import StaticHandler


class IndexVerifier:

    _errlog = ""

    def __init__(self):

        return

    @staticmethod
    def print_err_log():

        errmsg = "Here are the logs of the index file verification : \n" + IndexVerifier._errlog + "\n\n"

        print errmsg

        errfile = ValidatorGlobals.testdir + "/indexerrors.info"

        with open(errfile, "a+") as indxerr:
            indxerr.write(errmsg)

        return

    @staticmethod
    def _add_err_log(msgtype, msg):

        if msgtype == StaticHandler.MessageType.error:

            IndexVerifier._errlog += "\n ERROR - " + msg + "\n"

        elif msgtype == StaticHandler.MessageType.info:

            IndexVerifier._errlog += "\n INFO - " + msg + "\n"

        elif msgtype == StaticHandler.MessageType.success:

            IndexVerifier._errlog += "\n SUCCESS - " + msg + "\n"

        return

    @staticmethod
    def verify_index():

        t = {}
        idl = []

        indxverified = True
        IndexVerifier._errlog = ""

        with open(ValidatorGlobals.indxfile) as indxfile:
            indxdata = yaml.load(indxfile)

        for project in indxdata["Projects"]:

            IndexVerifier._add_err_log(StaticHandler.MessageType.info, "Verifying project entry : " + str(project))

            # Check for ID
            if "id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks an ID.")

            else:

                val = project["id"]

                if val not in idl:

                    idl.append(val)

                else:

                    indxverified = False
                    IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Duplicate entry")

            # Check for app-id
            if "app-id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks an app-id")

            else:

                print "App ID checks TBD"

            # Check for job-id
            if "job-id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks a job-id")


            # Check git-url
            if "git-url" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks a git-url")

            else:

                val = project["git-url"]

                if not StaticHandler.StaticHandler.is_valid_url(val):

                    indxverified = False
                    IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Git url is not a proper url")

            # Check git-path
            if "git-path" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks git-path")

            # Check git-branch
            if "git-branch" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks git-branch")

            # Check notify-email
            if "notify-email" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks a notify email.")

            else:

                print "notify-email checks TBD"

            # Checks depends-on
            if "depends-on" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log(StaticHandler.MessageType.error, "Entry lacks depends-on.")

            else:

                val = project["depends-on"]

                if val is not None:

                    for item in val:

                        if item not in idl:

                            indxverified = False
                            IndexVerifier._add_err_log(StaticHandler.MessageType.error, "One or more items is not an"
                                                                                        " existing project that appears"
                                                                                        " before this one in the index."
                                                       )
                            break

        return indxverified
