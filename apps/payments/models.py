from django.db import models
from common.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.


class Payment(TimeStampedModel):
    """
    Represents a single payment made towards an invoice.
    Supports partial payments and tracks payment methods.
    """
    # --- core related fields ---
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_("Invoice"),
    )
    # --- payment details fields ---
    amount = models.DecimalField(
        _("amount"),
        max_digits=10,
        decimal_places=2,
        validators=[models.MinValueValidator(0)],
        help_text=_("Amount paid towards the invoice."),
    )
    
    method = models.CharField(
        _("payment method"),
        max_length=50,
        choices=[
            ('cash', _('Cash')),
            ('bank_transfer', _('Bank Transfer')),
            ('card', _('Credit/Debit Card')),
            ('mobile_payment', _('Mobile Payment')),
            ('other', _('Other')),
        ],
        default='bank_transfer',
    )

    transaction_id = models.CharField(
        _("transaction ID"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Unique identifier for the payment transaction."),
    )

    paid_at = models.DateTimeField(
        _("payment date"),
        default=timezone.now,
        help_text=_("Date and time when the payment was made."),
    )

    notes = models.TextField(
        _("notes"),
        blank=True,
        help_text=_("Additional notes or details about the payment."),
    )

    def __str__(self):
        return f"Payment {self.id} - {self.amount} for Invoice {self.invoice.id}"
    
    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ['-paid_at']

    def clean(self):
        """
        Custom validation to prevent overpayment.
        """
        # Ensure we don't exceed the invoice amount
        if self.invoice:
            total_paid = self.invoice.total_paid
            # if this is a new payment (no pk), add its amount to the total.
            # if this is an existing payment (has pk), adjust the total accordingly.

            if self.pk:
                old_payment = Payment.objects.get(pk=self.pk)
                new_total_paid = total_paid - old_payment.amount + self.amount
            else:
                new_total_paid = total_paid + self.amount

            if new_total_paid > self.invoice.total_amount:
                raise ValidationError(
                    _('This payment would exceed the invoice total. '
                      'Total paid would be %(new_total)s, but the invoice total is %(invoice_total)s.') % 
                      {'new_total': new_total_paid, 'invoice_total': self.invoice.total_amount}
                )