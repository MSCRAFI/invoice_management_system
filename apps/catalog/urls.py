# catalog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product-list'),
    path('new/', views.ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product-update'),
]