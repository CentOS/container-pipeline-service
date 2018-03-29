import subprocess

from django.conf import settings
from django.db import models

from container_pipeline.models import Package, RepoInfo
from container_pipeline.utils import get_job_hash

"""
moduleauthor: The Container Pipeline Service Team

This module containers the django models that are common for the entire
service. Its purpose is to store data accross the entire service
"""

# TODO : Expand the models to include more metadata.


class Project(models.Model):
    """
    This is the model of the project type. It relates to the project table,
    which is used to store overall metadata of projects, created on the
    service
    """
    name = models.CharField(max_length=200, unique=True, db_index=True)
    target_file_link = models.CharField(max_length=350, default=None)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'projects'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.uuid = get_job_hash(self.name)
        return super(Project, self).save(*args, **kwargs)


class Build(models.Model):
    """
    This is a model used to store the metadata of every build triggered accross
    a paticular project on the service. This includes information like its
    state, when it was created/completed, where are the logs and so on.
    """

    uuid = models.CharField(max_length=100, unique=True, db_index=True)
    project = models.ForeignKey(Project)

    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('processing', 'In process'),
        ('complete', 'Complete'),
        ('error', 'Error'),
        ('failed', 'Failed')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              db_index=True, blank=True)

    logs = models.CharField(max_length=200, null=True)

    NOTIFICATION_STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    )
    weekly_scan = models.BooleanField(default=False)
    notification_status = models.CharField(
        max_length=20, choices=NOTIFICATION_STATUS_CHOICES, db_index=True,
        default='', blank=True)

    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    trigger = models.TextField(max_length=125, default=None,
                               null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    # field to contain link for pipeline service code logs if build fails
    service_debug_logs = models.CharField(
        max_length=100, blank=True, null=True, default=None)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'builds'

    def __str__(self):
        return '{}:{}'.format(self.project, self.uuid)


class BuildPhase(models.Model):
    """
    This model is used to store information about every phase of
    any paticular build. This includes information such as when
    the phase was created, started and so on.
    """
    build = models.ForeignKey(Build)
    PHASE_CHOICES = (
        ('dockerlint', 'Docker lint'),
        ('build', 'Build'),
        ('test', 'Test'),
        ('scan', 'Scan'),
        ('delivery', 'Delivery')
    )
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES,
                             db_index=True)
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('processing', 'In process'),
        ('requeuedparent', 'Re-queued due to parent'),
        ('complete', 'Complete'),
        ('error', 'Error'),
        ('failed', 'Failed')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              db_index=True, blank=True)
    log_file_path = models.CharField(max_length=100, blank=True, null=True,
                                     default=None)

    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'build_phases'

    def __str__(self):
        return '{}:{}'.format(self.build, self.phase)


class ContainerImage(models.Model):
    """
    This model is used to hold information about every container image
    This includes metadata about a container such as what packages were
    installed, when it was scanned and so on.
    """
    name = models.CharField(max_length=200, db_index=True,
                            help_text="Image name", unique=True)
    packages = models.ManyToManyField(Package, related_name='images',
                                      help_text="Packages")
    parents = models.ManyToManyField('self', symmetrical=False,
                                     help_text="Parent images")
    repoinfo = models.ForeignKey(RepoInfo, null=True)

    to_build = models.BooleanField(default=False, db_index=True,
                                   help_text='Whether to build image or not')
    scanned = models.BooleanField(default=False, db_index=True,
                                  help_text='Whether the image is scanner')
    last_scanned = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        db_table = 'container_images'
        app_label = 'container_pipeline'

    def __str__(self):
        return self.name

    @property
    def fullname(self):
        return '{}/{}'.format(settings.REGISTRY_ENDPOINT[0], self.name)

    @property
    def jobname(self):
        return self.name.replace(':', '-').replace('/', '-')

    def pull(self):
        docker_cmd = 'docker pull {name}'.format(name=self.fullname)
        return subprocess.check_output(docker_cmd, shell=True)

    def run(self, cmd):
        docker_cmd = (
            'docker run --rm --entrypoint "/bin/bash" {name} -c "{cmd}"'.
            format(name=self.fullname, cmd=cmd.replace('"', '\\"')))
        return subprocess.check_output(docker_cmd, shell=True)

    def remove(self):
        """Remove docker image"""
        docker_cmd = (
            'docker rmi -f {}'.format(self.fullname))
        return subprocess.check_output(docker_cmd, shell=True)

    def trigger_build(self):
        if settings.JENKINS_USERNAME:
            cmd = (
                'java -jar {} -s {} build {} --username {} --password {}'
                .format(
                    settings.JENKINS_CLI,
                    settings.JENKINS_ENDPOINT,
                    self.jobname,
                    settings.JENKINS_USERNAME,
                    settings.JENKINS_PASSWORD)
            )
        else:
            cmd = (
                'java -jar {} -s {} build {}'.format(
                    settings.JENKINS_CLI,
                    settings.JENKINS_ENDPOINT,
                    self.jobname)
            )

        subprocess.check_call(cmd, shell=True)
