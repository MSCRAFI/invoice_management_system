# billing/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import Http404
from django.utils import timezone

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, AddItemForm
from .services import mark_invoice_paid, add_invoice_item
from django.shortcuts import render

from django.http import HttpResponse, FileResponse, HttpResponseServerError
from django.core.mail import EmailMessage
from django.conf import settings

from .services import clone_invoice
from .utils import generate_invoice_pdf
import traceback

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    # select_related is a performance optimization
    queryset = Invoice.objects.select_related('customer').order_by('-issued_at')

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'
    # prefetch_related is another performance optimization for related sets
    queryset = Invoice.objects.prefetch_related('items__product').select_related('customer')

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # The services.py file handles creating the invoice number
        # For simplicity here, we let the model's default handle it
        messages.success(self.request, "Invoice created successfully. You can now add items.")
        return super().form_valid(form)

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status in [obj.Status.PAID, obj.Status.CANCELLED]:
            raise Http404("You cannot edit a paid or cancelled invoice.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Invoice updated successfully.")
        return super().form_valid(form)

# --- Custom Action Views ---

def add_item_to_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status in [invoice.Status.PAID, invoice.Status.CANCELLED]:
        raise Http404("Cannot add items to a paid or cancelled invoice.")
    
    if request.method == 'POST':
        form = AddItemForm(request.POST)
        if form.is_valid():
            try:
                add_invoice_item(invoice, form.cleaned_data['product'].id, form.cleaned_data['quantity'])
                messages.success(request, "Item added to invoice.")
            except ValueError as e:
                messages.error(request, str(e))
            return redirect('invoice-detail', pk=invoice.pk)
    else:
        form = AddItemForm()
    
    return render(request, 'billing/add_item_form.html', {'form': form, 'invoice': invoice})

def mark_invoice_as_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        try:
            mark_invoice_paid(invoice)
            messages.success(request, f"Invoice {invoice.invoice_number} marked as paid.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('invoice-detail', pk=invoice.pk)
    
    return render(request, 'billing/mark_paid_confirm.html', {'invoice': invoice})



# =========================================


# --- New Feature Views ---

def clone_invoice_view(request, pk):
    """Creates a clone of an existing invoice."""
    original_invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        try:
            # For simplicity, we'll set the due date to 30 days from now
            new_due_date = timezone.now().date() + timezone.timedelta(days=30)
            new_invoice = clone_invoice(original_invoice.id, new_due_date)
            messages.success(request, f"Invoice {new_invoice.invoice_number} has been created by cloning {original_invoice.invoice_number}.")
            return redirect('invoice-detail', pk=new_invoice.pk)
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('invoice-detail', pk=original_invoice.pk)


def download_invoice_pdf(request, pk):
    """Generates and returns an invoice as a PDF download."""
    try:
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Get the buffer from the utility function
        buffer = generate_invoice_pdf(invoice)

        # --- CRITICAL CHANGE ---
        # Create a HttpResponse with the correct content type
        response = HttpResponse(buffer, content_type='application/pdf')
        
        # Set the Content-Disposition header to force a download
        response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
        
        return response

    except Exception as e:
        # This will catch any error and show it in the browser for debugging
        error_message = f"An error occurred: {e}<br><br>{traceback.format_exc()}"
        return HttpResponseServerError(error_message)


def send_invoice_email(request, pk):
    """Emails the invoice PDF to the customer."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        try:
            pdf = generate_invoice_pdf(invoice)

            email = EmailMessage(
                subject=f"Invoice {invoice.invoice_number} from Your Company",
                body=f"Dear {invoice.customer.name},\n\nPlease find your attached invoice.\n\nThank you for your business.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.customer.email],
            )
            email.attach(f'Invoice_{invoice.invoice_number}.pdf', pdf, 'application/pdf')
            email.send()

            messages.success(request, f"Invoice {invoice.invoice_number} has been sent to {invoice.customer.email}.")
        except Exception as e:
            messages.error(request, f"Failed to send email. Error: {e}")

        return redirect('invoice-detail', pk=invoice.pk)

    return redirect('invoice-detail', pk=invoice.pk)