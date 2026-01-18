# catalog/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for the Product model."""
    
    list_display = ('name', 'unit_price', 'is_active', 'get_stock_status')
    list_filter = ('is_active', 'track_inventory')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    # Use readonly fields for calculated or context-dependent fields
    readonly_fields = ('get_stock_status',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'unit_price', 'is_active')
        }),
        (_('Inventory Control'), {
            'fields': ('track_inventory', 'stock_quantity'),
            'description': _('Enable inventory tracking for physical products. The stock quantity will be managed automatically when invoices are marked as paid.')
        }),
    )

    def get_stock_status(self, obj):
        """Displays stock only if inventory is being tracked."""
        if obj.track_inventory:
            return f"{obj.stock_quantity} units"
        return "N/A (Service)"
    get_stock_status.short_description = _('Stock Status')