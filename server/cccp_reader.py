#!/usr/bin/env python
import os
import yaml

def main():
  stream = open("/set_env/cccp.yml",'r')
  cccp_yml = yaml.load(stream)
  stream.close()
  
  print "==> Getting current directory"
  curr_dir = os.getcwd()
 
  print "==> Saving scripts for build process"
  
  for key, value in cccp_yml.iteritems():
    if(key == "job-id"):
        job_id = cccp_yml["job-id"]

    if(key == "test-skip"):
        test_skip = cccp_yml["test-skip"]
    
    if(key == "desired-tag"):
        desired_tag = cccp_yml["desired-tag"]

    if(key == "build-script"):
        build_script = cccp_yml["build-script"]
        os.symlink(os.path.join(curr_dir,build_script),"/usr/bin/build_script")
    
    if(key == "test-script"):
        test_script = cccp_yml["test-script"]
        if(test_skip != True):
            os.symlink(os.path.join(curr_dir,test_script),"/usr/bin/test_script")
    
    if(key == "delivery-script"):
        delivery_script = cccp_yml["delivery-script"]
        os.symlink(os.path.join(curr_dir,delivery_script),"/usr/bin/delivery_script")

  print "==> scripts saved"

if __name__ == '__main__':
  main()
