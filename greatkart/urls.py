"""
URL configuration for greatkart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from orders.dashboard import dashboard

# Importação para traduzir com segurança o título principal do Admin Honeypot
from django.apps import apps
apps.get_app_config('admin_honeypot').verbose_name = 'Tentativas de Invasão'

urlpatterns = [
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('securelogin/dashboard/', dashboard, name='admin_dashboard'),
    path('securelogin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('pages.urls')),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path("shipping/", include("shipping.urls")),
    path('coupons/', include('coupons.urls')),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest.json'),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

# ⚠️ SÓ NO FINAL DO ARQUIVO:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
