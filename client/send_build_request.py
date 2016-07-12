#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting build details from jenkins"
build_details = {}
build_details['name'] = sys.argv[1]
build_details['tag']  = sys.argv[2]
build_details['depends_on'] = sys.argv[3]
build_details['action'] = "start_build"

print "Pushing bild details in the tube"
bs = beanstalkc.Connection(host="openshift")
bs.use("master_tube")
bs.put(json.dumps(build_details))
print "build details is pushed to master tube"
