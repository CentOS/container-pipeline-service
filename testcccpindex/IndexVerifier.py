#!/bin/python

import yaml
from TestGlobals import TestGlobals


class IndexVerifier:

    _errlog = ""

    def __init__(self):

        return

    @staticmethod
    def print_err_log():

        errmsg = "Here are the errors we found in the index file : \n" + IndexVerifier._errlog + "\n\n"

        print errmsg

        errfile = TestGlobals.testdir + "/indexerrors.info"

        with open(errfile, "a+") as indxerr:
            indxerr.write(errmsg)

        return

    @staticmethod
    def _add_err_log(msg):

        IndexVerifier._errlog += "\n LOG - " + msg + "\n"

        return

    @staticmethod
    def verify_index():

        t = {}
        idl = []

        indxverified = True
        IndexVerifier._errlog = ""

        with open(TestGlobals.indxfile) as indxfile:
            indxdata = yaml.load(indxfile)

        for project in indxdata["Projects"]:

            IndexVerifier._add_err_log("Verifying project entry : " + str(project))

            # Check for ID
            if "id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log("Entry lacks an ID.")

            else:

                if project["id"] not in idl:

                    idl.append(project["id"])

                else:

                    indxverified = False
                    IndexVerifier._add_err_log("Duplicate entry")

            # Check for app-id
            if "app-id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log("Entry lacks an app-id")

            else:
                print "check 2"

            # Check for job-id
            if "job-id" not in project.keys():

                indxverified = False
                IndexVerifier._add_err_log("Entry lacks a job-id")

            else:
                print "check 3"

        return indxverified
