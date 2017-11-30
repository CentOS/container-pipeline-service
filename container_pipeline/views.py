from container_pipeline.models.pipeline import Project, Build, BuildPhase
from rest_framework import viewsets
from container_pipeline.serializers import ProjectSerializerV1, BuildSerializerV1, BuildPhaseSerializerV1


DEFAULT_PROJECT_SERIALIZER = ProjectSerializerV1
DEFAULT_BUILD_SERIALIZER = BuildSerializerV1
DEFAULT_BUILD_PHASE_SERIALIZER = BuildPhaseSerializerV1


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()

    def get_serializer_class(self):
        if self.request.version == "v1":
            return ProjectSerializerV1
        else:
            return DEFAULT_PROJECT_SERIALIZER


class BuildViewSet(viewsets.ModelViewSet):
    queryset = Build.objects.all().order_by('start_time')

    def get_serializer_class(self):
        if self.request.version == "v1":
            return BuildSerializerV1
        else:
            return DEFAULT_BUILD_SERIALIZER


class BuildPhaseViewSet(viewsets.ModelViewSet):
    queryset = BuildPhase.objects.all().order_by('start_time')

    def get_serializer_class(self):
        if self.request.version == "v1":
            return BuildPhaseSerializerV1
        else:
            return DEFAULT_BUILD_PHASE_SERIALIZER
