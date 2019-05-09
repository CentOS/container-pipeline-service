FROM registry.centos.org/openshift/jenkins-slave-base-centos7

ADD Dockerfiles/ccp-openshift-slave/build_buildah.sh /tmp

RUN yum update -y && \
    yum install -y PyYAML python-requests docker mailx postfix epel-release && \
    yum install -y npm && \
    yum clean all && \
    npm install -g dockerfile_lint && \
    sh /tmp/build_buildah.sh && \
    rm -rf /tmp/build_buildah.sh /tmp/buildah

ENV BASH_ENV=/opt/rh/go-toolset-7/enable \
    ENV=/opt/rh/go-toolset-7/enable \
    PROMPT_COMMAND=". /opt/rh/go-toolset-7/enable"

ADD ./ /opt/ccp-openshift/
VOLUME ["/opt/ccp-openshift/ccp/scanning", "/var/lib/containers"]
