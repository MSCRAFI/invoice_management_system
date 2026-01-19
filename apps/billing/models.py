from django.db import models
from common.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F
from django.core.validators import MinValueValidator

import datetime
import random

# Create your models here.


class Invoice(TimeStampedModel):
    """
    Represents an invoice issued to a customer for products or services.
    """

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        SENT = 'SENT', _('Sent')
        PAID = 'PAID', _('Paid')
        OVERDUE = 'OVERDUE', _('Overdue')
        CANCELLED = 'CANCELLED', _('Cancelled')
    # Relationship Fields ---
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name=_("Customer"),
        help_text=_("The customer to whom this invoice is issued."),
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        verbose_name=_("Created By"),
    )
    # --- Core Invoice Fields ---
    invoice_number = models.CharField(
        _("invoice number"),
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text=_("Unique identifier for the invoice."),
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_("Current status of the invoice."),
    )
    # --- Date Fields ---
    issued_at = models.DateField(
        _("date issued"),
        default=timezone.now,
    )

    due_at = models.DateField(
        _("due at"),
    )
    # --- Financial (Denormalized for performance) ---
    subtotal = models.DecimalField(
        _("subtotal"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Total amount before taxes and discounts."),
    )

    tax_amount = models.DecimalField(
        _("tax amount"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        _("total amount"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Total amount due including taxes and discounts."),
    )
    # --- Optional Fields ---
    notes = models.TextField(
        _("notes"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        ordering = ['-issued_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"
    
    def clean(self):
        """
        Prevent modification of invoices that are already paid or cancelled.
        """

        if self.pk:
            # Fetch the current status from the database to compare
            original_status = Invoice.objects.get(pk=self.pk).status
            if original_status in [self.Status.PAID, self.Status.CANCELLED]:
                raise ValidationError(
                    _("You cannot modify an invoice that is %(status)s.") % 
                    {'status': original_status}
                )
            
        # In your Invoice class
    def save(self, *args, **kwargs):
        # Only generate an invoice number if this is a new object (no pk yet)
        if not self.pk:
            # Generate a unique invoice number
            today = datetime.date.today()
            year_day = today.strftime("%Y%m%d")
            random_suffix = random.randint(1000, 9999)
            self.invoice_number = f"INV-{year_day}-{random_suffix}"
        
        # Call the "real" save method
        super().save(*args, **kwargs)
            
    @property
    def balance_due(self):
        """Calculate the remaining balance due on the invoice after payments."""
        total_paid = self.payments.aggregate(sum=Sum('amount'))['sum'] or 0
        return self.total_amount - total_paid
    
    @property
    def is_past_due(self):
        """Check if the invoice is past its due date and not yet paid."""
        return self.due_at < timezone.now().date() and self.status != self.Status.PAID

class InvoiceItem(TimeStampedModel):
    """
    Represents a single line item on an invoice.
    """
    # --- Relationship Field ---
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Invoice"),
    )

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        related_name='invoice_items',
        verbose_name=_("Product"),
    )
    # --- Core Item Fields ---
    description = models.TextField(
        _("description"),
        help_text=_("Description of the product or service. Defaults to product description."),
    )

    quantity = models.PositiveIntegerField(
        _("quantity"),
        default=1,
        validators=[MinValueValidator(1)],
    )

    unit_price = models.DecimalField(
        _("unit price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_("Price at the time of invoicing. Does not change."),
    )
    # --- Calculated Field ---
    total = models.DecimalField(
        _("total price"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Total price for this line item (quantity x unit price)."),
    )

    class Meta:
        verbose_name = _("invoice item")
        verbose_name_plural = _("invoice items")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} on {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        """
        Override save to populate fields and calculate totals.
        """
        # set description from product if not provided
        if not self.description and self.product:
            self.description = self.product.description
        # calculate total price
        self.total = self.quantity * self.unit_price

        super().save(*args, **kwargs)