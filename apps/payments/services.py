# payments/services.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Payment
from apps.billing.models import Invoice
from django.db import models
from django.core.exceptions import ValidationError


# --- Core Payment Services ---

@transaction.atomic
def record_payment(
    invoice_id: int,
    amount: Decimal,
    method: str,
    paid_at: timezone.datetime = None,
    transaction_id: str = None,
    notes: str = None
) -> Payment:
    """
    Records a new payment for a given invoice.

    Args:
        invoice_id: The ID of the invoice being paid.
        amount: The payment amount.
        method: The payment method (e.g., 'bank_transfer').
        paid_at: The datetime of the payment. Defaults to now.
        transaction_id: Optional unique transaction ID from a gateway.
        notes: Optional notes for the payment.

    Returns:
        The newly created Payment object.

    Raises:
        ValueError: If the invoice is not found, already paid, or the payment
                    would result in an overpayment.
    """
    try:
        invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    except Invoice.DoesNotExist:
        raise ValueError(_("Invoice with ID %(id)s does not exist.") % {'id': invoice_id})

    # Prevent payment on cancelled invoices
    if invoice.status == Invoice.Status.CANCELLED:
        raise ValueError(_("Cannot record a payment for a cancelled invoice."))

    # Check for overpayment before creating the payment object
    current_total_paid = get_total_paid(invoice)
    if (current_total_paid + amount) > invoice.total_amount:
        raise ValidationError(
            _('Payment amount of %(amount)s exceeds the outstanding balance of %(balance)s.') % 
            {'amount': amount, 'balance': invoice.balance_due}
        )

    # Create the payment
    payment = Payment.objects.create(
        invoice=invoice,
        amount=amount,
        method=method,
        paid_at=paid_at or timezone.now(),
        transaction_id=transaction_id,
        notes=notes
    )

    # --- Side Effect: Update Invoice Status ---
    # After payment is recorded, check if the invoice is now fully paid.
    new_balance = get_balance_due(invoice)
    if new_balance <= 0 and invoice.status != Invoice.Status.PAID:
        # Use a direct update to avoid triggering model save() side effects
        Invoice.objects.filter(pk=invoice.id).update(status=Invoice.Status.PAID)

    return payment


# --- Information & Query Services ---

def get_total_paid(invoice: Invoice) -> Decimal:
    """
    Calculates the total amount paid for a given invoice.
    
    Args:
        invoice: The Invoice object.

    Returns:
        A Decimal representing the total amount paid. Returns 0.00 if no payments exist.
    """
    # Use aggregate to sum up all payment amounts for the invoice
    result = invoice.payments.aggregate(total=models.Sum('amount'))['total']
    # The result can be None if there are no payments, so we coalesce to 0
    return result or Decimal('0.00')


def get_balance_due(invoice: Invoice) -> Decimal:
    """
    Calculates the remaining balance for a given invoice.

    Args:
        invoice: The Invoice object.

    Returns:
        A Decimal representing the outstanding balance.
    """
    # This is a simple calculation based on the total and the amount paid.
    # It relies on the get_total_paid service to centralize the logic.
    total_paid = get_total_paid(invoice)
    return invoice.total_amount - total_paid
