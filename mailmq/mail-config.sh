#!/bin/bash
export REPLYTO=container-build@centos.org
mkfifo /var/spool/postfix/public/pickup
postfix start
sleep 30
echo "Test email from local machine" | mail -r container-build-report@centos.org -s "cccp-build is complete" bamachrn@gmail.com

sleep 30
/bin/bash
