FROM registry.centos.org/centos/centos:latest

LABEL INSTALL='docker run -ti --rm --privileged -v /etc/atomic.d/:/host/etc/atomic.d/ $IMAGE sh /install.sh'

# Install python-docker-py to spin up container using scan script
RUN yum -y update && yum -y install python-docker-py && yum clean all

ADD rpm-verify /
ADD rpm_verify.py /
ADD install.sh /
