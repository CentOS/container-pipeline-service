FROM registry.centos.org/centos/centos:latest

MAINTAINER CentOS Community Container Pipeline <centos-devel@centos.org>

#RUN yum update -y && \
RUN yum install epel-release -y && \
    yum install python PyYAML python-pip postgresql-devel  -y && \
    yum remove epel-release -y && \
    yum clean all

RUN pip install raven --upgrade && pip install django==1.11.2 psycopg2==2.7.3 \
 djangorestframework drfdocs django-filter

RUN mkdir -p /opt/cccp-service
ADD node.kubeconfig ca.crt /opt/cccp-service/
ADD container_pipeline /opt/cccp-service/container_pipeline
ADD oc /usr/bin/oc

ENV PYTHONPATH=$PYTHONPATH:/opt/cccp-service/
WORKDIR /opt/cccp-service
