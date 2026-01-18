# customers/services.py

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .models import Customer

@transaction.atomic
def deactivate_customer(customer_id: int) -> Customer:
    """
    Deactivates a customer instead of deleting them to preserve data integrity.
    """
    try:
        customer = Customer.objects.get(pk=customer_id)
        customer.is_active = False
        customer.save()
        return customer
    except Customer.DoesNotExist:
        raise ValueError(_("Customer with ID %(id)s does not exist.") % {'id': customer_id})
