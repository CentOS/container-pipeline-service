FROM registry.centos.org/centos/centos

LABEL INSTALL='docker run --rm --privileged -v /etc/atomic.d:/host/etc/atomic.d/ $IMAGE sh /install.sh'

RUN yum -y update && \
    yum -y install epel-release && \
    yum -y install atomic python-docker-py && \
    yum clean all

ADD container-capabilities-scanner run_scanner.py scanner.py install.sh /
