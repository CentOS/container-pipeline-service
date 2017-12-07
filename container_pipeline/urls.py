from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from container_pipeline import views

apiv1router = routers.DefaultRouter()
apiv1router.register(r'projects', views.ProjectViewSetV1)
apiv1router.register(r'builds', views.BuildViewSetV1)
apiv1router.register(r'build-phases', views.BuildPhaseViewSetV1)

urlpatterns = [
    url(r'^api/v1/', include(apiv1router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^api/schema/', include('rest_framework_docs.urls')),
]
