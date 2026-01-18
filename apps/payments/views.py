# payments/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView

from apps.billing.models import Invoice
from .forms import PaymentForm
from .services import record_payment
from .models import Payment

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 30
    queryset = Payment.objects.select_related('invoice').order_by('-paid_at')

def record_new_payment(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if invoice.status == Invoice.Status.CANCELLED:
        messages.error(request, "Cannot record payment for a cancelled invoice.")
        return redirect('invoice-detail', pk=invoice.pk)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                record_payment(
                    invoice_id=invoice.id,
                    amount=form.cleaned_data['amount'],
                    method=form.cleaned_data['method'],
                    transaction_id=form.cleaned_data['transaction_id'],
                    notes=form.cleaned_data['notes']
                )
                messages.success(request, "Payment recorded successfully.")
                return redirect('invoice-detail', pk=invoice.pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        # Pre-fill the amount with the balance due
        initial = {'amount': invoice.balance_due}
        form = PaymentForm(initial=initial)
    
    return render(request, 'payments/payment_form.html', {'form': form, 'invoice': invoice})