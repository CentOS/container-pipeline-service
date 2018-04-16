#!/usr/bin/env bash

if [ $1 == "apache" ]; then
    exec /usr/sbin/httpd -DFOREGROUND;
else
    exec $@
fi