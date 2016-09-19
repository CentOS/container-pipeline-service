#!/usr/bin/env python

import beanstalkc
import json
import sys

print "Getting image details from test phase"
beanstalk_host = sys.argv[1]
output_image = sys.argv[2]
notify_email = sys.argv[3]

msg_details = {}
msg_details['action'] = "notify_user"
msg_details['subject'] = "SUCCESS: Your container build request is complete"
msg_details['msg'] = "Build is successful. You can pull the image ("+output_image+")"
msg_details['to_email'] = notify_email
msg_details['subject'] = "cccp-build is complete"
msg_details['msg'] = ("Build is successful please "
                      "pull the image (%s) " % output_image)

print "Pushing notification details to master_tube"
bs = beanstalkc.Connection(host=beanstalk_host)
bs.use("master_tube")
bs.put(json.dumps(msg_details))
print "Notification details pushed to master_tube"
