from django.db import models
from common.models import TimeStampedModel, SoftDeleteModel
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Customer(TimeStampedModel, SoftDeleteModel):
    """
    Represents a client or customer to whom invoices are issued.
    Supports soft-deletion to preserve historical data integrity.
    """
    # --- Core Customer Fields ---
    name = models.CharField(
        _("name"),
        max_length=255,
        db_index=True,
        help_text=_("Name of the customer."),
    )

    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        help_text=_("Email address of the customer."),
    )

    phone = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Contact phone number of the customer."),
    )

    address = models.TextField(
        _("address"),
        blank=True,
        null=True,
        help_text=_("Physical address of the customer."),
    )
    # --- Status Field ---
    is_active = models.BooleanField(
        _("active status"),
        default=True,
        help_text=_(
            "Designates whether this customer is active. "
            "Unselect this instead of deleting customers to preserve data integrity."
        ),
    )

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @property
    def is_inactive(self):
        """Check if the customer is inactive."""
        return not self.is_active