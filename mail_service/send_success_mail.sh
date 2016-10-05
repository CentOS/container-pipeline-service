#!/bin/bash
echo $3 |mail -r container-build-report@centos.org -s "$1" $2
