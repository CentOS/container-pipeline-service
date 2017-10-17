#!/bin/bash
echo -e $3 |mail -r container-build-reports@centos.org -c container-status-report@centos.org -S smtp=smtp://mail.centos.org -s "$1" $2
