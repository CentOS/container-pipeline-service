#!/usr/bin/bash

#This script gets the latest nginx access logs. Retrieves docker pull counts
#for the images and stores it to file system. If the count file is already
#existing, this gets the count from the stored value and adds new retrieved
# value. The sum of both is stored back to the file system.
#
#For now the count file system is stored under the /var/image-count/
#

#Create a tmp dir to do all the processings
log_process_location="/tmp/registry-stat-processing/"
mkdir -p $log_process_location
cd $log_process_location

#Get nginx access logs to tmp
filename=`ls /var/log/nginx/access.log-*.gz|tail -1`
echo $filename
cp $filename $log_process_location

#Get the file name and start processing
filename=`ls access.log-*.gz|tail -1`
gunzip $filename
filename=${filename%.gz}
echo $filename

#filter out requests came through docker client and processed successfully
grep docker $filename|grep -v 404| grep manifests|awk '{print $7}' > docker-access.log

#Now for each unique image name get the count if it has the tag with it.
#if the image does not have a tag and has sha revision then figure out the tag
#from the revision and add the count to the tag.
for i in `cat docker-access.log|sort -u`
do
     pull_count=`grep $i docker-access.log|wc -l`
     if [[ $i == *"sha256"* ]]
     then
         digest=`echo $i|awk -F':' '{print $2}'`
         namespace=`echo $i|awk -F'/' '{print $2"/repositories/"$3"/"$4"/"}'`
         tag_name="not-found"
         if [[ $namespace == *"manifests"* ]];then
             namespace=`echo $i|awk -F'/' '{print $2"/repositories/"$3"/"}'`
             tag_link=`grep $digest /var/lib/registry/docker/registry/$namespace/_manifests/ -R|grep tags`
             tag_name=`echo $tag_link|awk -F'/' '{print $13}'`
         else
             tag_link=`grep $digest /var/lib/registry/docker/registry/$namespace/_manifests/ -R|grep tags`
             tag_name=`echo $tag_link|awk -F'/' '{print $14}'`
         fi

         manifest=`echo $i|awk -F':' '{print $1}'`
         manifest=`echo ${manifest%/sha256}`
         i=`echo "$manifest/$tag_name"`
     fi
     i=`echo $i|sed -e "s/\/v2\///g"|sed -e "s/\/manifests\//\//g"`
     file_location=`echo "/var/image-count/$i"`

     if [[ -f "$file_location/count" ]]
     then
         existing_count=`cat $file_location/count`
         pull_count=$(($pull_count+$existing_count))
         rm -f $file_location/count
     fi

     mkdir -p $file_location
     echo $pull_count > $file_location/count
     echo "pull count $pull_count image $i" >>analysis-data.txt
done

#stats has been collected and processed now remove the tmp dir
rm -rf $log_process_location
