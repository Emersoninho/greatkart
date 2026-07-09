from django.urls import path
from .views import calculate_shipping

urlpatterns = [
    path("calculate/", calculate_shipping, name="calculate_shipping"),
]