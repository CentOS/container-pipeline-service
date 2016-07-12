#!/bin/bash
export REPLYTO=container-build@centos.org
mkfifo /var/spool/postfix/public/pickup
postfix start
sleep 20
python /mail_service/worker_notify_user.py
