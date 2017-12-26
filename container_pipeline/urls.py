from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
import container_pipeline.api as api

urlpatterns = [
    url(r'^admin/', admin.site.urls)
]

urlpatterns += api.get_urls()

urlpatterns += [
    url(r'^api/schema/', include('rest_framework_docs.urls'))
]
