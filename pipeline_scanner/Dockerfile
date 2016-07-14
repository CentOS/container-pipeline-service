FROM centos:centos7

LABEL INSTALL='docker run -it --rm --privileged -v /etc/atomic.d:/host/etc/atomic.d/ $IMAGE sh /install.sh'

# Install python-docker-py to spin up container using scan script
RUN yum -y update && yum -y install python-docker-py && yum clean all

ADD pipeline-scanner /
ADD scanner.py /
ADD install.sh /
