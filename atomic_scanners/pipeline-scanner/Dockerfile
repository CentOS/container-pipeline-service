FROM centos:centos7

LABEL INSTALL='docker run -it --rm --privileged -v /etc/atomic.d:/host/etc/atomic.d/ $IMAGE sh /install.sh'

RUN yum -y update && yum clean all

ADD pipeline-scanner /
ADD scanner.py /
ADD install.sh /
