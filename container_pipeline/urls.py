from django.conf.urls import url, include
from django.contrib import admin
import container_pipeline.api.v1.routes as v1_routes

apiv1router = v1_routes.init_router()

urlpatterns = [
    url(r'^api/v1/', include(apiv1router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^api/schema/', include('rest_framework_docs.urls')),
]
