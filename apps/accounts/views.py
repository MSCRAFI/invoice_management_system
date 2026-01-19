from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.db.models import Sum, Count, F
from django.utils import timezone

from .forms import CustomLoginForm
from apps.billing.models import Invoice
from apps.payments.models import Payment
from apps.catalog.models import Product
from apps.reports.services import get_monthly_revenue, get_total_due, get_invoice_status_counts, get_top_customers


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- Core Metrics ---
        context['total_invoices'] = Invoice.objects.count()
        context['paid_invoices'] = Invoice.objects.filter(status=Invoice.Status.PAID).count()
        context['total_revenue'] = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_due'] = get_total_due()

        # --- Actionable Lists ---
        context['overdue_invoices'] = Invoice.objects.filter(
            due_at__lt=timezone.now().date()
        ).exclude(status__in=[Invoice.Status.PAID, Invoice.Status.CANCELLED]).select_related('customer')[:5]

        context['top_customers'] = get_top_customers(limit=5)

        # Low stock alert (products with less than 10 units)
        context['low_stock_products'] = Product.objects.filter(
            track_inventory=True
        ).filter(stock_quantity__lt=10).order_by('stock_quantity')[:5]

        # --- Data for Charts ---
        # Monthly Revenue (for the last 12 months)
        monthly_revenue_qs = get_monthly_revenue(years=1)
        context['revenue_chart_labels'] = [item['month'].strftime('%b %Y') for item in monthly_revenue_qs]
        context['revenue_chart_data'] = [float(item['revenue']) for item in monthly_revenue_qs]

        # Invoice Status Breakdown
        status_counts = get_invoice_status_counts()
        context['status_chart_labels'] = [dict(Invoice.Status.choices).get(status, status) for status in status_counts.keys()]
        context['status_chart_data'] = list(status_counts.values())

        return context