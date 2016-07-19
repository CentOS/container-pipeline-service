#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting image details from test phase"
beanstalk_host = sys.argv[1]
notify_email  = sys.argv[2]

msg_details = {}
msg_details['action'] = "notify_user"
msg_details['subject'] = "Container-build failed"
msg_details['msg'] = "Container build failed due to error in status of build or test steps"
msg_details['to_mail'] = notify_email


print "Pushing notification details to master_tube"
bs = beanstalkc.Connection(host=beanstalk_host)
bs.use("master_tube")
bs.put(json.dumps(msg_details))
print "notification details pushed to master_tube"
