#!/bin/bash
echo -e $3 |mail -r container-build-report@centos.org -a $4 -s "$1" $2
