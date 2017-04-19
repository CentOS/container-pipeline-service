if [ -f env.properties ]; then
    rm env.properties
fi
touch env.properties
echo "PYTHONPATH=$(pwd):$PYTHONPATH" >> env.properties

bash provisions/utils/gencert.sh registry.centos.org || true
echo -e  'y\n'| ssh-keygen -t rsa -N "" -f provisions/jenkins.key
