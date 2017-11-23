from container_pipeline.models.pipeline import Project, Build, BuildPhase
from rest_framework import viewsets
from container_pipeline.serializers import ProjectSerializer, BuildSerializer, BuildPhaseSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class BuildViewSet(viewsets.ModelViewSet):
    queryset = Build.objects.all().order_by('start_time')
    serializer_class = BuildSerializer


class BuildPhaseViewSet(viewsets.ModelViewSet):
    queryset = BuildPhase.objects.all().order_by('start_time')
    serializer_class = BuildPhaseSerializer
