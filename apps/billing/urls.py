# billing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.InvoiceListView.as_view(), name='invoice-list'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('new/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice-update'),
    path('<int:pk>/add-item/', views.add_item_to_invoice, name='invoice-add-item'),
    path('<int:pk>/mark-paid/', views.mark_invoice_as_paid, name='invoice-mark-paid'),
]