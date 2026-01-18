from .models import Invoice, InvoiceItem
from django.db import transaction
from django.db import models
from decimal import Decimal
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.catalog.models import Product


# --- Core Calculation Service ---

@transaction.atomic
def recalculate_invoice_total(invoice: Invoice):
    """
    Recalculates and saves the subtotal, tax, and total for an invoice.
    This function is atomic to prevent data corruption.
    """
    # Use aggregate to get the sum of all item totals for this invoice
    items_total = invoice.items.aggregate(
        total_sum=models.Sum('total')
    )['total_sum'] or 0.0

    invoice.subtotal = items_total

    tax_rate = 0.1  # Assume a fixed tax rate of 10% for simplicity
    invoice.tax_amount = invoice.subtotal * tax_rate
    invoice.total_amount = invoice.subtotal + invoice.tax_amount

    # We use save() without calling the full save() method to avoid
    # triggering the clean() validation if the invoice is locked.
    # This is safe because this is an internal calculation.

    Invoice.objects.filter(pk=invoice.pk).update(
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount
    )





# --- Invoice Creation & Management Services ---

def _generate_unique_invoice_number() -> str:
    """Generates a simple, unique invoice number."""
    # In a real-world app, this might be more complex, e.g., INV-YYYY-NNNN
    # For this blueprint, a UUID is a robust and simple choice.
    return f"INV-{uuid.uuid4().hex[:8].upper()}"

@transaction.atomic
def create_invoice(customer_id: int, created_by_user, due_date: timezone.datetime.date) -> Invoice:
    """
    Creates a new draft invoice for a given customer.
    """
    from customers.models import Customer # Avoid circular import
    try:
        customer = Customer.objects.get(pk=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise ValueError(_("Customer with ID %(id)s does not exist or is inactive.") % {'id': customer_id})

    invoice = Invoice.objects.create(
        customer=customer,
        created_by=created_by_user,
        invoice_number=_generate_unique_invoice_number(),
        status=Invoice.Status.DRAFT,
        due_at=due_date,
        # Subtotal, tax, and total will be 0 by default
    )
    return invoice


@transaction.atomic
def add_invoice_item(invoice: Invoice, product_id: int, quantity: int) -> InvoiceItem:
    """
    Adds a product as a new item to an existing invoice.
    Locks the invoice if it's not in a modifiable state.
    """
    if invoice.status in [Invoice.Status.PAID, Invoice.Status.CANCELLED]:
        raise ValueError(_("Cannot add items to a %(status)s invoice.") % {'status': invoice.status})

    try:
        product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        raise ValueError(_("Product with ID %(id)s does not exist or is inactive.") % {'id': product_id})

    # Check inventory if applicable
    if product.track_inventory and product.stock_quantity < quantity:
        raise ValueError(_("Not enough stock for '%(product)s'. Available: %(stock)s, Requested: %(qty)s.") % 
                         {'product': product.name, 'stock': product.stock_quantity, 'qty': quantity})

    # Create the invoice item with a price snapshot
    item = InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        quantity=quantity,
        unit_price=product.unit_price, # Price is captured here
    )

    # The post_save signal will automatically trigger recalculate_invoice_total
    return item


@transaction.atomic
def remove_invoice_item(invoice_item_id: int) -> None:
    """
    Removes an invoice item.
    """
    try:
        item = InvoiceItem.objects.get(pk=invoice_item_id)
        invoice = item.invoice
        if invoice.status in [Invoice.Status.PAID, Invoice.Status.CANCELLED]:
            raise ValueError(_("Cannot remove items from a %(status)s invoice.") % {'status': invoice.status})
        item.delete()
        # The post_delete signal will automatically trigger recalculate_invoice_total
    except InvoiceItem.DoesNotExist:
        raise ValueError(_("Invoice item with ID %(id)s does not exist.") % {'id': invoice_item_id})


@transaction.atomic
def mark_invoice_paid(invoice: Invoice) -> Invoice:
    """
    Marks an invoice as paid and updates inventory for tracked products.
    """
    if invoice.status == Invoice.Status.PAID:
        raise ValueError(_("Invoice %(number)s is already marked as paid.") % {'number': invoice.invoice_number})
    
    if invoice.status == Invoice.Status.CANCELLED:
        raise ValueError(_("Cannot mark a cancelled invoice as paid."))

    # Update inventory for each item on the invoice
    for item in invoice.items.all():
        if item.product.track_inventory:
            # Use F() expressions to prevent race conditions
            Product.objects.filter(pk=item.product.pk).update(
                stock_quantity=models.F('stock_quantity') - item.quantity
            )

    # Update the invoice status
    invoice.status = Invoice.Status.PAID
    invoice.save() # Use save() to trigger any potential post_save logic for the invoice itself

    return invoice
