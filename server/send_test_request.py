#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting build details from jenkins"
image_details = {}
image_details['name'] = sys.argv[1]
image_details['tag']  = sys.argv[2]

print "Pushing image details in the tube"
bs = beanstalkc.Connection(host="openshift")
bs.use("start_test")
bs.put(json.dumps(image_details))
print "image details is pushed to tube for testing"
