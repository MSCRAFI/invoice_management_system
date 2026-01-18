# payments/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for the Payment model."""
    
    list_display = ('invoice_link', 'amount', 'method', 'paid_at', 'transaction_id')
    list_filter = ('method', 'paid_at')
    search_fields = ('invoice__invoice_number', 'transaction_id')
    ordering = ('-paid_at',)
    
    readonly_fields = ('invoice',)
    raw_id_fields = ('invoice',) # Use raw_id for performance

    def invoice_link(self, obj):
        """Displays a clickable link to the invoice admin page."""
        if obj.invoice:
            url = reverse('admin:billing_invoice_change', args=[obj.invoice.id])
            return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
        return "-"
    invoice_link.short_description = _('Invoice')
    invoice_link.admin_order_field = 'invoice__invoice_number'