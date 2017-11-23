from rest_framework import serializers
from container_pipeline.models.pipeline import Project, Build, BuildPhase


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = {
            'name', 'created', 'last_updated'
        }


class BuildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Build
        fields = {
            'uuid', 'project', 'status', 'logs', 'notification_status', 'start_time',
            'end_time', 'trigger', 'created', 'last_updated', 'service_debug_log'
        }


class BuildPhaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BuildPhase
        fields = {
            'build', 'phase', 'status', 'log_file_path', 'start_time', 'end_time',
            'created', 'last_updated'
        }
