from django.urls import path
from . import views

urlpatterns = [
    path('products', views.getProducts, name='getProducts'),  # Accessible at /api/products
    path('', views.getRoutes, name='getRoutes'),  # Accessible at /api/
]
