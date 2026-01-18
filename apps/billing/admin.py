# billing/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Invoice, InvoiceItem
from .services import recalculate_invoice_total


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for managing InvoiceItems directly on the Invoice page."""
    model = InvoiceItem
    extra = 1  # Number of empty forms to display
    readonly_fields = ('total',)
    fields = ('product', 'description', 'quantity', 'unit_price', 'total')

    def get_readonly_fields(self, request, obj=None):
        # Make 'unit_price' readonly if the invoice is locked
        if obj and obj.status in [Invoice.Status.PAID, Invoice.Status.CANCELLED]:
            return ('product', 'description', 'quantity', 'unit_price', 'total')
        return self.readonly_fields


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin configuration for the Invoice model."""
    
    list_display = ('invoice_number', 'customer_link', 'status_badge', 'total_amount', 'issued_at', 'due_at')
    list_filter = ('status', 'issued_at')
    search_fields = ('invoice_number', 'customer__name', 'customer__email')
    ordering = ('-issued_at',)
    
    inlines = [InvoiceItemInline]
    
    # Use raw_id_fields for performance on large tables
    raw_id_fields = ('customer', 'created_by')
    
    # Fields that should be automatically calculated or set
    readonly_fields = ('subtotal', 'tax_amount', 'total_amount', 'balance_due_display')
    
    fieldsets = (
        (_('Invoice Details'), {
            'fields': ('invoice_number', 'customer', 'status', 'created_by')
        }),
        (_('Dates'), {
            'fields': ('issued_at', 'due_at')
        }),
        (_('Financial Summary'), {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'balance_due_display'),
            'classes': ('collapse',), # Make this section collapsible
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def customer_link(self, obj):
        """Displays a clickable link to the customer admin page."""
        if obj.customer:
            url = reverse('admin:customers_customer_change', args=[obj.customer.id])
            return format_html('<a href="{}">{}</a>', url, obj.customer.name)
        return "-"
    customer_link.short_description = _('Customer')
    customer_link.admin_order_field = 'customer__name'

    def status_badge(self, obj):
        """Displays the status with a color-coded badge."""
        colors = {
            Invoice.Status.DRAFT: 'gray',
            Invoice.Status.SENT: 'blue',
            Invoice.Status.PAID: 'green',
            Invoice.Status.OVERDUE: 'red',
            Invoice.Status.CANCELLED: 'black',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def balance_due_display(self, obj):
        """Displays the calculated balance due."""
        return f"{obj.balance_due:.2f}"
    balance_due_display.short_description = _('Balance Due')

    def save_model(self, request, obj, form, change):
        """Automatically set the created_by field on creation."""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Recalculate invoice total after items are saved."""
        formset.save()
        if formset.instance:
            recalculate_invoice_total(formset.instance)
            # Refresh the instance to get the new totals
            formset.instance.refresh_from_db()

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly if the invoice is paid or cancelled."""
        if obj and obj.status in [Invoice.Status.PAID, Invoice.Status.CANCELLED]:
            # Return a list of all field names
            return [field.name for field in self.model._meta.fields] + ['balance_due_display']
        return self.readonly_fields

    # Custom admin action
    @admin.action(description=_('Mark selected invoices as Sent'))
    def mark_as_sent(self, request, queryset):
        updated = queryset.filter(status=Invoice.Status.DRAFT).update(status=Invoice.Status.SENT)
        self.message_user(request, _('%(count)d invoices were successfully marked as sent.') % {'count': updated})
    
    actions = [mark_as_sent]