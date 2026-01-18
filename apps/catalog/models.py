from django.db import models
from common.models import TimeStampedModel, SoftDeleteModel
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

# Create your models here.


class Product(TimeStampedModel, SoftDeleteModel):
    """
    Represents a product or a service that can be billed on an invoice.
    Can optionally track inventory for physical products.
    """
    # --- Core Product Fields ---
    name = models.CharField(
        _("name"),
        max_length=255,
        db_index=True,
        help_text=_("Name of the product or service."),
    )

    description = models.TextField(
        _("description"),
        blank=True,
        null=True,
        help_text=_("Detailed description of the product or service."),
    )

    unit_price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_("The price per single unit."),
    )
    # --- Inventory Tracking Field ---
    track_inventory = models.BooleanField(
        _("track inventory"),
        default=False,
        help_text=_(
            "Check this if this is a physical product. "
            "Uncheck for services or non-stocked items."
        ),
    )

    stock_quantity = models.PositiveIntegerField(
        _("stock quantity"),
        null=True,
        blank=True,
        help_text=_(
            "Current stock level. Applicable only if inventory tracking is enabled."
        ),
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this product/service is available for invoicing. "
            "Unselect this instead of deleting products to preserve data integrity."
        ),
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Custom validation to ensure data consistency between inventory tracking and stock quantity.
        """
        # if we are not tracking inventory, stock_quantity must be empty
        if not self.track_inventory and self.stock_quantity is not None:
            raise ValidationError(
                {
                    'stock_quantity': _(
                        'Stock quantity should not be set when "Track inventory" is disabled.'
                    )
                }
            )
        # if we are tracking inventory, stock_quantity must be set
        if self.track_inventory and self.stock_quantity is None:
            raise ValidationError(
                {
                    'stock_quantity': _(
                        'Stock quantity is required when "Track inventory" is enabled.'
                    )
                }
            )