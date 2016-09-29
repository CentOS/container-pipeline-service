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
 
  got_build_script = 0;
  got_test_script = 0;
  got_delivery_script = 0;

  for key, value in cccp_yml.iteritems():
    if(key == "job-id"):
      job_id = cccp_yml["job-id"]

    if(key == "test-skip"):
      test_skip = cccp_yml["test-skip"]
    
    if(key == "build-script"):
      build_script_path = cccp_yml["build-script"]
      os.symlink(os.path.join(curr_dir,build_script_path),"/build_script")
      got_build_script=1;
    
    if(key == "test-script"):
      test_script = cccp_yml["test-script"]
      if(test_skip != True):
        os.symlink(os.path.join(curr_dir,test_script),"/test_script")
        got_test_script=1;
    
    if(key == "delivery-script"):
      delivery_script = cccp_yml["delivery-script"]
      os.symlink(os.path.join(curr_dir,delivery_script),"/delivery_script")
      got_delivery_script=1;

  if(got_build_script == 0):
    echo_scripts("/build_script","Build ");

  if(got_test_script == 0):
    echo_scripts("/test_scripts","Test ");

  if(got_delivery_script == 0):
    echo_scripts("/delivery_scripts","Delivery ");


  print "==> scripts saved"

def echo_scripts(filepath,phase):
  fo = open(filepath,"w")
  fo.write("echo \""+phase+"Script not present\"")
  fo.close()

if __name__ == '__main__':
  main()
