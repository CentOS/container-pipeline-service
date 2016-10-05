#!/bin/bash
mail -r container-build-report@centos.org -s "$1" $2 < $3
