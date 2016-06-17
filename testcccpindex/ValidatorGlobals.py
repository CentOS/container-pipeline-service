#!/bin/python

import os


class ValidatorGlobals:
    """Contains constants being used by the script"""

    def __init__(self):

        return

    # This path can be modified by user and it is where the test data will be stored
    # This includes the index file, the repos and test logs
    testdir = os.path.abspath("./cccp-index-test")

    giveexitcode = False
    indexonly = False
    exitcode = 0

    # If using a local index, just change the path here tpo match that of your index file
    indxfile = testdir + "/index" + "/index.yml"
    customindexused = testdir + "/.customindex"

    # If need to alter the giturl, edit this
    indexgit = "https://github.com/kbsingh/cccp-index.git"