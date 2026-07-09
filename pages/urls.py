from django.urls import path
from . import views

urlpatterns = [
    path('termos/', views.termos_uso, name='termos'),
    path('privacidade/', views.privacidade, name='privacidade'),
    path('trocas/', views.trocas_devolucoes, name='trocas'),
]