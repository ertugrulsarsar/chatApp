"""
URL configuration for chatApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def home_page_view(request):
    """Projenin ana karşılama sayfasını gösterir."""
    return render(request, 'home.html')

urlpatterns = [
    path("", home_page_view, name="home"),
    path("admin/", admin.site.urls),
    path("users/", include('users.urls')),  # Kullanıcı yönetimi
    path("chat/", include('chat.urls')),
]

# Media files için URL pattern'leri (sadece development için)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
