#!/usr/bin/env python
import os
import yaml
from shutil import copyfile

def main():
  stream = open("cccp.yml",'r')
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
    
    if(key == "build-script"):
      build_script_path = cccp_yml["build-script"]
      os.symlink(os.path.join(curr_dir,build_script_path),"/usr/bin/build_script")
    else:
      echo_scripts("/usr/bin/build_script","Build")
    
    if(key == "test-script"):
      test_script = cccp_yml["test-script"]
      if(test_skip != True):
        os.symlink(os.path.join(curr_dir,test_script),"/usr/bin/test_script")
    else:
      echo_scripts("/usr/bin/test_script","Test")
    
    if(key == "delivery-script"):
      delivery_script = cccp_yml["delivery-script"]
      os.symlink(os.path.join(curr_dir,delivery_script),"/usr/bin/delivery_script")
    else:
      echo_scripts("/usr/bin/delivery_script","Delivery")

  print "==> scripts saved"

def echo_scripts(filepath,phase):
  fo = open(filepath,"w")
  fo.write("echo \""+phase+"Script not present\"")
  fo.close()

if __name__ == '__main__':
  main()
