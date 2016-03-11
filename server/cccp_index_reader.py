#!/usr/bin/env python
import os
import yaml

stream = open("ci.centos.org.yaml",'r')
index_yaml = yaml.load(stream)
stream.close()

project_name = index_yaml[0]["project"]["name"]
image_name = index_yaml[0]["project"]["image_name"]
build_script = index_yaml[0]["project"]["build_script"]
test_location = index_yaml[0]["project"]["test_location"]
test_script = index_yaml[0]["project"]["test_script"]
delivery_script = index_yaml[0]["project"]["delivery_script"]

print "==> Saving scripts for build process"
os.symlink(build_script,"/usr/bin/build_script")
os.symlink(test_script,"/usr/bin/test_script")
os.symlink(delivery_script,"/usr/bin/delivery_Script")
print "==> scripts saved"

