#!/bin/bash
export REPLYTO=container-build@centos.org
mkfifo /var/spool/postfix/public/pickup
postfix start
sleep 30
echo $1 | mail -r container-build-report@centos.org -s $1 $2
sleep 30
