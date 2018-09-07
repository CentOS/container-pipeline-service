This directory contains the Dockerfile and source for the container image,
which is going to be used as scanning module for scan stage in pipeline
for every build request in the OpenShift cluster and weekly scan.

The resulting container is scheduled as Pod using DaemonSet on every possible
builder node of OpenShift cluster. The container exposes a docker-volume
on the node, where its scheduled.
The exposed volume contains scanning module responsible for performing scans.
The exposed volume can then be used by other containers to access the scanning
module, perform scans and grab the results.
