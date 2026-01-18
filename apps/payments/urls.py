# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('invoice/<int:invoice_pk>/new/', views.record_new_payment, name='payment-create'),
]