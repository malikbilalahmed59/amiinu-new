
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/suggestions/', include('suggestions.urls')),
    path('api/sourcing/', include('sourcing.urls')),
    path('api/',include('shipments.urls')),
    path('api/warehouse/',include('warehouse.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

