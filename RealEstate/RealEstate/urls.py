from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('estate.urls')),
    path('estate/', include('estate.urls')),
]

# Добавляем эту строку в самый конец, чтобы отдавать картинки при разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)