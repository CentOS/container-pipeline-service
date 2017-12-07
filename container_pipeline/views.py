from container_pipeline.models.pipeline import Project, Build, BuildPhase
from rest_framework import viewsets
from container_pipeline.serializers import ProjectSerializerV1, BuildSerializerV1, BuildPhaseSerializerV1

# API V1


class ProjectViewSetV1(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializerV1


class BuildViewSetV1(viewsets.ModelViewSet):
    queryset = Build.objects.all().order_by('start_time')
    serializer_class = BuildSerializerV1


class BuildPhaseViewSetV1(viewsets.ModelViewSet):
    queryset = BuildPhase.objects.all().order_by('start_time')
    serializer_class = BuildPhaseSerializerV1

# API V1 ends
