from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.billing.models import Invoice
from apps.payments.models import Payment


def get_monthly_revenue(years: int = 2):
    """
    Returns a queryset of monthly revenue for the last N years.
    """
    start_date = timezone.now().date() - timedelta(days=365 * years)
    
    revenue = (
        Payment.objects
        .filter(paid_at__date__gte=start_date, invoice__status=Invoice.Status.PAID)
        .annotate(month=TruncMonth('paid_at'))
        .values('month')
        .annotate(revenue=Sum('amount'))
        .order_by('month')
    )
    return revenue


def get_total_due():
    """
    Calculates the total outstanding balance across all active (non-paid, non-cancelled) invoices.
    """
    total_due = (
        Invoice.objects
        .exclude(status__in=[Invoice.Status.PAID, Invoice.Status.CANCELLED])
        .annotate(
            balance=F('total_amount') - Sum('payments__amount')
        )
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    return total_due


def get_invoice_status_counts():
    """
    Returns a breakdown of invoice counts by their status.
    """
    counts = (
        Invoice.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    # Convert to a more usable dictionary format
    return {item['status']: item['count'] for item in counts}


def get_top_customers(limit: int = 5):
    """
    Returns the top N customers by total amount paid.
    """
    top_customers = (
        Invoice.objects
        .values('customer__name', 'customer__id')
        .annotate(total_spent=Sum('payments__amount'))
        .filter(total_spent__isnull=False) # Exclude customers who haven't paid anything
        .order_by('-total_spent')[:limit]
    )
    return top_customers