#!/bin/bash
echo $2 | mail -r container-build-report@centos.org -s "$1" $3
