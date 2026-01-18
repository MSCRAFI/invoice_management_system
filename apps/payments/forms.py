# payments/forms.py

from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    """
    Form for recording a new payment. The invoice is set from the URL.
    """
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'transaction_id', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }