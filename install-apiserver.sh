#!/usr/bin/env bash

HTTPD_CONF="/etc/httpd/conf/httpd.conf"
HTTPD_WELCOME="/etc/httpd/conf.d/welcome.conf"
APACHE_RUNTIME_DIR="/opt/apache_run"
CODE_BASE_PATH="/opt/cccp-service"
CODE_PATH="${CODE_BASE_PATH}/container_pipeline/"
WSGI_PATH="${CODE_PATH}/wsgi.py"
PIDFILE="${APACHE_RUNTIME_DIR}/httpd.pid"
STATIC_FILES="${CODE_BASE_PATH}/static/"

yum -y install httpd mod_wsgi;
mkdir -p ${APACHE_RUNTIME_DIR};
chown -R apache:apache ${CODE_BASE_PATH};
chown -R apache:apache ${APACHE_RUNTIME_DIR};

# Fix-up Configurations
rm -rf ${HTTPD_WELCOME};
sed -i 's/^Listen 80/Listen 8080\\\nListen 8443/g' ${HTTPD_CONF};
sed -i 's/^Listen 8080\\/Listen 8080/g' ${HTTPD_CONF};
#sed -i 's/^Group apache/Group root/g' ${HTTPD_CONF};
sed -i 's/logs\/error_log/\/dev\/stderr/g' ${HTTPD_CONF};
sed -i 's/logs\/access_log/\/dev\/stdout/g' ${HTTPD_CONF};
mkdir -p /etc/httpd/logs && touch /etc/httpd/logs/error_log && touch /etc/httpd/logs/access_log;

cat <<EOF >> ${HTTPD_CONF}
DefaultRuntimeDir ${APACHE_RUNTIME_DIR}
PidFile ${PIDFILE}
WSGIScriptAlias / ${WSGI_PATH}
WSGIPythonPath ${CODE_BASE_PATH}
Alias /static/ ${STATIC_FILES}

<Directory ${CODE_PATH}>
<Files wsgi.py>
Require all granted
</Files>
</Directory>
<Directory ${STATIC_FILES}>
Require all granted
</Directory>
EOF

chmod -R 777 /etc/httpd/logs;
