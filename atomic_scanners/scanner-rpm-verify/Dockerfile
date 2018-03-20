FROM registry.centos.org/centos/centos

LABEL INSTALL='docker run --rm --privileged -v /etc/atomic.d/:/host/etc/atomic.d/ $IMAGE sh /install.sh'

RUN yum -y update && yum clean all

ADD rpm-verify rpm_verify.py install.sh /
