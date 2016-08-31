# Continuous Integration

## Setup

- Install jenkins-job-builder: ``sudo yum install python2-jenkins-job-builder -y``
- Configure ``/etc/jenkins_jobs/jenkins_jobs.ini`` Jenkins Job Builder as follows:
    ```
[jenkins]
user=<jenkins user>
password=<jenkins password>
url=<jenkins endpoint, e.g. https://ci.centos.org>

    ```

## Usage

```
jenkins-jobs update ci/job.yml
```
