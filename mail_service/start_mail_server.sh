#!/bin/bash
export REPLYTO=container-build-reports@centos.org
mkfifo /var/spool/postfix/public/pickup
postfix start
sleep 20
python /opt/cccp-service/mail_service/worker_notify_user.py
