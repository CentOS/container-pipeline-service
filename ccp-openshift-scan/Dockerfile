FROM registry.centos.org/centos/centos:latest

RUN yum -y update && yum clean all

ADD scanning /opt/scanning

VOLUME ["/opt/scanning"]

CMD ["/bin/tail", "-f", "/dev/null"]
