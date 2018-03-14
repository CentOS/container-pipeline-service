FROM registry.centos.org/centos/centos

LABEL INSTALL='docker run --rm --privileged -v /etc/atomic.d:/host/etc/atomic.d/ $IMAGE sh /install.sh'

RUN yum -y update && \
    yum -y install python-docker-py && \
    yum clean all

ADD misc-package-updates scanner.py install.sh /
