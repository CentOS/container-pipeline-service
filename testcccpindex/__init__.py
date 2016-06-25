#!/bin/bash

import sys
from ValidatorGlobals import ValidatorGlobals
from Engine import IndexValidator
import yaml

if __name__ == '__main__':
    rs = IndexValidator().run()

    print "\nTests completed\n"
    resultsfile = ValidatorGlobals.testdir + "/results.yml"

    with open(resultsfile, "w") as resfile:
        yaml.dump(rs, resfile, default_flow_style=False)

    print "\nYou can view the test results at " + resultsfile + "\n"

#    if not ValidatorGlobals.holdbackexitcode:

    if ValidatorGlobals.exitcode > 0:

        sys.exit(1)

    else:

        sys.exit(0)
