from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),          # Django built-in admin panel
    path('', include('main.urls')),           # barcha app URL lari
]

# Media fayllar (rasm, PDF) uchun

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
