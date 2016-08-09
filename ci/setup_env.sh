if [ -f env.properties ]; then
    rm env.properties
fi
touch env.properties
echo "URL_BASE=http://admin.ci.centos.org:8080" >> env.properties
echo "API=$(cat ~/duffy.key)" >> env.properties

bash utils/gencert.sh registry.centos.org || true
echo -e  'y\n'| ssh-keygen -t rsa -N "" -f jenkins.key
