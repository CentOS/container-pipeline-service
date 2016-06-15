#!/bin/bash

import sys
from TestGlobals import TestGlobals
from Engine import Tester
import yaml

if __name__ == '__main__':
    rs = Tester().run()

    print "\nTests completed\n"
    resultsfile = TestGlobals.testdir + "/results.yml"

    with open(resultsfile, "w") as resfile:
        yaml.dump(rs, resfile, default_flow_style=False)

    print "\nYou can view the test results at " + resultsfile + "\n"

    if TestGlobals.giveexitcode:
        sys.exit(TestGlobals.exitcode)