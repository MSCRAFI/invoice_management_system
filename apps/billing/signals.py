from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Invoice, InvoiceItem
from .services import recalculate_invoice_total
from apps.catalog.models import Product
from django.db import models

@receiver(post_save, sender=InvoiceItem)
@receiver(post_delete, sender=InvoiceItem)
def update_invoice_on_item_change(sender, instance, **kwargs):
    """
    When an invoice item is saved or deleted, recalculate the parent invoice's total.
    """
    if instance.invoice:
        recalculate_invoice_total(instance.invoice)

@receiver(post_save, sender=InvoiceItem)
def handle_invoice_status_change(sender, instance, created, **kwargs):
    """
    Handles logic when an invoice's status changes, like updating inventory.
    """
    # We only care about updates, not new creations
    if not created:
        try:
            # Get the old status from the database before the save
            old_instance = Invoice.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status

            # Get the old status from the database before the save
            if old_status != Invoice.Status.PAID and new_status == Invoice.Status.PAID:
                for item in instance.items.all():
                    if item.product.track_inventory:
                        Product.objects.filter(pk=item.product.pk).update(
                            stock_quantity=models.F('stock_quantity') - item.quantity
                        )
        except Invoice.DoesNotExist:
            # Handle cases where the invoice might have been deleted
            pass  # Invoice was just created, no old status to compare