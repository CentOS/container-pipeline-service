from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from container_pipeline.pipeline_api.urls import get_api_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls)
]

urlpatterns += get_api_urls()

urlpatterns += [
    url(r'^api/schema/', include('rest_framework_docs.urls'))
]
