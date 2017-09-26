#!/bin/bash
echo -e $3 |mail -r container-build-report@centos.org -c container-status-report@centos.org -S smtp=smtp://mail.centos.org -s "$1" $2
