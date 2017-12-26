from rest_framework import routers
from django.conf.urls import url, include
import container_pipeline.api as api
import container_pipeline.api.v1.views as v1_views


V1_ENDPOINT = api.API_ENDPOINT + r'/v1'
PACKAGES_ENDPOINT = V1_ENDPOINT + r'/packages'
RPM_ENDPOINT = PACKAGES_ENDPOINT + r'/rpms'


def get_urls():
    urls = []

    router1 = routers.DefaultRouter()
    router1.register(r'projects', v1_views.ProjectViewSet)
    router1.register(r'builds', v1_views.BuildViewSet)
    router1.register(r'build-phases', v1_views.BuildPhaseViewSet)
    router1.register(r'container-image', v1_views.ContainerImageViewSet)
    urls += url(V1_ENDPOINT, include(router1.urls))

    router2 = routers.DefaultRouter()
    router2.register(r'package', v1_views.PackageViewSet)
    router2.register(r'repo-info', v1_views.RepoInfoViewSet)
    urls += url(RPM_ENDPOINT, include(router2.urls))

    return urls
