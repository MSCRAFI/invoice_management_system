# billing/forms.py
from django import forms
from .models import Invoice
from apps.catalog.models import Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'issued_at', 'due_at', 'notes']
        widgets = {
            'issued_at': forms.DateInput(attrs={'type': 'date'}),
            'due_at': forms.DateInput(attrs={'type': 'date'}),
        }

class AddItemForm(forms.Form):
    product = forms.ModelChoiceField(queryset=None, label="Product/Service")
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)