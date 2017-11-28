from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from container_pipeline import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'builds', views.BuildViewSet)
router.register(r'build-phases', views.BuildPhaseViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/schema/', include('rest_framework_docs.urls')),
    url(r'^admin/', admin.site.urls)
]
