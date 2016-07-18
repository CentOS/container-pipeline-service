if [ -f env.properties ]; then
    rm env.properties
fi
touch env.properties
echo "URL_BASE=http://admin.ci.centos.org:8080" >> env.properties
echo "API=914f27e6-84a0-11e5-b2e3-525400ea212d" >> env.properties

bash utils/gencert.sh registry.centos.org || true
echo -e  'y\n'| ssh-keygen -t rsa -N "" -f jenkins.key
