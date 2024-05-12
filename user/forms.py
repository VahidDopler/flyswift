from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import MyUserModel, Gender, formatted_countries


class ChargingAccountForm(forms.Form):
    value = forms.IntegerField(min_value=10000, max_value=9999999999999999,
                               label="Value of charging account", initial=10000),
    credit_card_number = forms.IntegerField(min_value=1000000000000000, max_value=9999999999999999,
                                            label="Credit card number")
    credit_card_holder_name = forms.CharField(required=True, max_length=40)
    expiration_month = forms.IntegerField(min_value=1, max_value=12, label="Expiration month (MM)")
    expiration_year = forms.IntegerField(min_value=2023, max_value=2030, label="Expiration year (YYYY)")
    cvv = forms.IntegerField(min_value=100, max_value=999, label="CVV")

    def clean(self):
        cleaned_data = super().clean()

        # Validate the expiration date
        month = cleaned_data['expiration_month']
        year = cleaned_data['expiration_year']
        ccn = cleaned_data['credit_card_number']
        ccv_number = cleaned_data['cvv']
        if not (1 <= month <= 12):
            raise ValidationError({'expiration_month': ['Invalid expiration month.']})

        if not (2023 <= year <= 2030):
            raise ValidationError({'expiration_year': ['Invalid expiration year.']})
        if not (1000000000000000 <= ccn <= 9999999999999999):
            raise ValidationError({"credit_card_number": ["invalid credit card number."]})
        if not (100 <= ccv_number <= 999):
            raise ValidationError({"cvv_number": ["invalid credit card cvv number."]})
        return cleaned_data


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = MyUserModel
        fields = ['username', 'email', 'full_name', 'phone', 'gender', 'country', 'address', 'password1',
                  'password2', 'role']
        exclude = ("charge", )

    def __init__(self, *args, **kwargs):
        super(MyUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['email'].label = 'Email'
        self.fields['full_name'].label = 'full_name'
        self.fields['phone'].label = 'Phone'
        self.fields['gender'].label = 'Gender'
        self.fields['country'].label = 'Country'
        self.fields['address'].label = 'address'

    def clean_email(self):
        email = self.cleaned_data['email']
        if MyUserModel.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use. Please use a different email.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if MyUserModel.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different username.")
        return username



