# customers/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for the Customer model."""
    
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('name',)
    
    # Add a direct link to view all invoices for a customer
    def invoice_count(self, obj):
        count = obj.invoices.count()
        if count > 0:
            url = reverse('admin:billing_invoice_changelist') + f'?customer__id__exact={obj.id}'
            return format_html('<a href="{}">{} Invoices</a>', url, count)
        return "0 Invoices"
    invoice_count.short_description = _('Invoices')

    # Add the custom method to the list display
    list_display = ('name', 'email', 'phone', 'invoice_count', 'is_active')