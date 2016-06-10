FROM centos

RUN yum -y update

RUN yum -y install docker

RUN yum -y install wget mailx postfix rsync

ADD mail-config.sh /usr/bin/

RUN chmod 777 /usr/bin/mail-config.sh

CMD mail-config.sh
