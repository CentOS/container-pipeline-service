FROM registry.centos.org/openshift/jenkins-slave-base-centos7

RUN yum install -y PyYAML && \
    yum install -y docker atomic atomic-registries && \
    yum install -y mailx && \
    yum install -y epel-release && \
    yum install -y npm && \
    yum clean all && \
    npm install -g dockerfile_lint
