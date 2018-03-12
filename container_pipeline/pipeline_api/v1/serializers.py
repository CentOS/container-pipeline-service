from rest_framework import serializers

from container_pipeline.models.pipeline import Project, Build, BuildPhase, \
    ContainerImage
from container_pipeline.models.tracking import RepoInfo, Package

"""
moduleauthor: The Container Pipeline Service Team

This module contains Model Serializers for v1 api of the service
service. Its purpose is to serialize the models so that api views
can make use of the data.
"""


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Project model.
    """

    class Meta:
        model = Project
        fields = (
            'name',
            'created',
            'last_updated'
        )


class BuildSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Build model.
    """

    class Meta:
        model = Build
        fields = (
            'project',
            'status',
            'logs',
            'weekly_scan',
            'notification_status',
            'start_time',
            'end_time',
            'trigger',
            'created',
            'last_updated',
            'service_debug_logs'
        )


class BuildPhaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the BuildPhase model.
    """

    class Meta:
        model = BuildPhase
        fields = (
            'build',
            'phase',
            'status',
            'log_file_path',
            'start_time',
            'end_time',
            'created',
            'last_updated'
        )


class RepoInfoSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the RepoInfo model.
    """

    class Meta:
        model = RepoInfo
        fields = (
            'baseurls',
            'basearch',
            'releasever',
            'infra'
        )


class PackageSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Package model.
    """

    class Meta:
        model = Package
        fields = (
            'name',
            'arch',
            'version',
            'release',
            'created',
            'last_updated'
        )


class ContainerImageSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the ContainerImage model.
    """

    class Meta:
        model = ContainerImage
        fields = (
            'name',
            'packages',
            'parents',
            'repoinfo',
            'to_build',
            'scanned',
            'last_scanned',
            'created',
            'last_updated'
        )
