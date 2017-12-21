from rest_framework import routers
import container_pipeline.api.v1.views as v1_views


def init_router():
    router = routers.DefaultRouter()
    router.register(r'projects', v1_views.ProjectViewSet)
    router.register(r'builds', v1_views.BuildViewSet)
    router.register(r'build-phases', v1_views.BuildPhaseViewSet)
    return router