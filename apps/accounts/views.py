# accounts/views.py
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import CustomLoginForm

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
        # Add summary data for the dashboard
        from apps.billing.models import Invoice
        from apps.payments.models import Payment
        from django.db.models import Sum, Count
        
        context['total_invoices'] = Invoice.objects.count()
        context['paid_invoices'] = Invoice.objects.filter(status=Invoice.Status.PAID).count()
        context['total_revenue'] = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['recent_invoices'] = Invoice.objects.select_related('customer').order_by('-issued_at')[:5]
        return context