from django.db import models

from container_pipeline.utils import get_job_hash


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)
    uuid = models.CharField(max_length=100, unique=True, db_index=True,
                            blank=True)

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
    notification_status = models.CharField(
        max_length=20, choices=NOTIFICATION_STATUS_CHOICES, db_index=True,
        default='', blank=True)

    start_time = models.DateTimeField(default=None, blank=True)
    end_time = models.DateTimeField(default=None, blank=True)

    trigger = models.CharField(max_length=20, default=None, blank=True)
    trigger_details = models.TextField(max_length=100, default=None,
                                       blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'builds'

    def __str__(self):
        return '{}:{}'.format(self.project, self.uuid)


class BuildPhase(models.Model):
    build = models.ForeignKey(Build)
    PHASE_CHOICES = (
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
        ('complete', 'Complete'),
        ('error', 'Error'),
        ('failed', 'Failed')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              db_index=True, blank=True)

    start_time = models.DateTimeField(default=None, blank=True)
    end_time = models.DateTimeField(default=None, blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'build_phases'

    def __str__(self):
        return '{}:{}'.format(self.build, self.phase)
