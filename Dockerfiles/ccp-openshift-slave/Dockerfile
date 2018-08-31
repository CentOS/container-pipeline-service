FROM registry.centos.org/openshift/jenkins-slave-base-centos7

RUN yum install -y PyYAML docker mailx epel-release && \
    yum install -y npm && \
    yum clean all && \
    npm install -g dockerfile_lint

ADD ./ /opt/ccp-openshift/
