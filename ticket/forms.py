from django import forms
from django.core.exceptions import ValidationError

class CreditCardForm(forms.Form):
    credit_card_number = forms.IntegerField(label="Credit card number")
    credit_card_holder_name = forms.CharField(required=True, max_length=40)
    expiration_month = forms.IntegerField(label="Expiration month (MM)")
    expiration_year = forms.IntegerField(label="Expiration year (YYYY)")
    cvv = forms.IntegerField(label="CVV")
    seat_number = forms.IntegerField(min_value=1, label="seat_number")

    def clean(self):
        cleaned_data = super().clean()

        # Validate the expiration date
        month = cleaned_data['expiration_month']
        year = cleaned_data['expiration_year']
        ccn = cleaned_data['credit_card_number']
        ccv_number = cleaned_data['cvv']
        if not (1 <= month <= 12):
            raise Exception({'invalid expiration_month'})

        if not (2023 <= year <= 2030):
            raise Exception({'invalid expiration_year'})
        if not (1000000000000000 <= ccn <= 9999999999999999):
            raise Exception({"invalid credit_card_number"})
        if not (100 <= ccv_number <= 999):
            raise Exception({"invalid cvv_number"})
        return cleaned_data
