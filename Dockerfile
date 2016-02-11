FROM centos

RUN curl --silent --location https://rpm.nodesource.com/setup_5.x | bash - && yum -y install nodejs 

#adding all the source code to /data/artifact
RUN mkdir -p "/data/artifact"
WORKDIR /data/artifact/

#Adding the required source code and dependencies for running the application

#for CI
#ADD node_modules node_modules
ADD models models
ADD html html
ADD routes routes
ADD tests tests
ADD app.js package.json ./
RUN npm install

VOLUME ['./tmp']
 
EXPOSE 3010
CMD [node app.js]
