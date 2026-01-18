from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from .models import Product

@transaction.atomic
def decrease_stock(product_id: int, quantity: int) -> Product:
    """
    Atomically decreases the stock quantity for a given product.
    Raises an error if the product is not found or if there is insufficient stock.
    """
    if quantity <= 0:
        raise ValueError(_("Quantity to decrease must be a positive number."))

    try:
        # Use select_for_update to lock the row and prevent race conditions
        product = Product.objects.select_for_update().get(pk=product_id)

        if not product.track_inventory:
            raise ValueError(_("Product '%(name)s' does not track inventory.") % {'name': product.name})

        if product.stock_quantity < quantity:
            raise ValueError(
                _("Insufficient stock for '%(name)s'. Available: %(available)s, Required: %(required)s.") % 
                {'name': product.name, 'available': product.stock_quantity, 'required': quantity}
            )
        
        # Use F() expression for an atomic database-level update
        Product.objects.filter(pk=product_id).update(stock_quantity=F('stock_quantity') - quantity)
        
        # Refresh the instance to get the new value
        product.refresh_from_db()
        return product

    except Product.DoesNotExist:
        raise ValueError(_("Product with ID %(id)s does not exist.") % {'id': product_id})