#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting image details from test phase"
beanstalk_host = sys.argv[1]

msg_details = {}
msg_details["action"] = "notify_user"
msg_details["output_image"] = sys.argv[2]
msg_details["notify_email"] = sys.argv[3]
msg_details["TEST_TAG"] = sys.argv[4]
msg_details["build_status"] = True

print "Pushing notification details to master_tube"
bs = beanstalkc.Connection(host=beanstalk_host)
bs.use("master_tube")
bs.put(json.dumps(msg_details))
print "Notification details pushed to master_tube"
