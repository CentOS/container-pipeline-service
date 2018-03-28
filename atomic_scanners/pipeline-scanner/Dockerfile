FROM registry.centos.org/centos/centos:latest

LABEL INSTALL='docker run --rm --privileged -v /etc/atomic.d:/host/etc/atomic.d/ $IMAGE sh /install.sh'

RUN yum -y update && yum clean all

ADD pipeline-scanner scanner.py install.sh /
