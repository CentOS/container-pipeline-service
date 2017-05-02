"""
This is a constants file for rpm-verify atomic scanner
In this file, one can mention the files to be excluded in end
result of scanner OR Any other expected property configuration
changes
"""


# Filter the paths you know the resulting image or base image itself
# has issue about and need to be filtered
# out since this is a known issue and it is in progress to get fixed.
FILTER_PATHS = [
  "/",   # centos base image has issue with this filepath
]


# Filter filepaths starting with following directories listing,
# since these paths are expected to be modified and should not
# take into account

FILTER_DIRS = [
    "/var", "/run", "/media", "/mnt", "/tmp", "/proc", "/sys", "/boot"
]
