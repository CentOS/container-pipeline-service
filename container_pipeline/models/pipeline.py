from django.db import models

from container_pipeline.utils import get_job_hash


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)

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

    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    trigger = models.CharField(max_length=20, default=None, blank=True,
                               null=True)
    trigger_details = models.TextField(max_length=100, default=None,
                                       null=True, blank=True)

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
        ('complete', 'Complete'),
        ('error', 'Error'),
        ('failed', 'Failed')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              db_index=True, blank=True)

    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = 'container_pipeline'
        db_table = 'build_phases'

    def __str__(self):
        return '{}:{}'.format(self.build, self.phase)


# class PackageX(models.Model):
#     name = models.CharField(max_length=200, db_index=True,
#                             help_text="Package name")
#     arch = models.CharField(max_length=20, db_index=True,
#                             help_text="Architecture")
#     version = models.CharField(max_length=100, help_text="Version")
#     release = models.CharField(max_length=100, help_text="Release")
#
#     created = models.DateTimeField(auto_now_add=True, blank=True)
#     last_updated = models.DateTimeField(auto_now=True, blank=True)
#
#     class Meta:
#         db_table = 'packagesx'
#         unique_together = ('name', 'arch', 'version', 'release')
#         app_label = 'container_pipeline'
#
#     def __str__(self):
#         return "{}-{}-{}.{}".format(self.name, self.version, self.release,
#                                     self.arch)
#
#
# class RepoInfoX(models.Model):
#     baseurls = models.TextField(max_length=2000, db_index=True,
#                                 help_text="Repo urls", unique=True)
#     basearch = models.CharField(max_length=20, db_index=True)
#     releasever = models.CharField(max_length=10, db_index=True)
#     infra = models.CharField(max_length=50)
#
#     class Meta:
#         db_table = 'repo_infox'
#         app_label = 'container_pipeline'
#
#     def __str__(self):
#         return self.baseurls
#
#
# class ContainerImageX(models.Model):
#     name = models.CharField(max_length=200, db_index=True,
#                             help_text="Image name", unique=True)
#     packages = models.ManyToManyField(PackageX, related_name='images',
#                                       help_text="Packages")
#     parents = models.ManyToManyField('self', symmetrical=False,
#                                      help_text="Parent images")
#     repoinfo = models.ForeignKey(RepoInfoX, null=True)
#
#     to_build = models.BooleanField(default=False, db_index=True,
#                                    help_text='Whether to build image or not')
#     scanned = models.BooleanField(default=False, db_index=True,
#                                   help_text='Whether the image is scanner')
#     last_scanned = models.DateTimeField(null=True, blank=True)
#
#     created = models.DateTimeField(auto_now_add=True, blank=True)
#     last_updated = models.DateTimeField(auto_now=True, blank=True)
#
#     class Meta:
#         db_table = 'container_images'
#         app_label = 'container_pipeline'
#
#     def __str__(self):
#         return self.name
