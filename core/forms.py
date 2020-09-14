from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from localflavor.us.forms import USStateSelect

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)

class CheckoutForm(forms.Form):
    customer_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    email_address = forms.EmailField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_city = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'custom-select d-block w-100',
    }))
    shipping_state = forms.CharField(widget=USStateSelect(attrs={
        'class': 'custom-select d-block w-100',
    }))
    # shipping_country = CountryField(blank_label='(select country)').formfield(
    #     required=False,
    #     widget=CountrySelectWidget(attrs={
    #         'class': 'custom-select d-block w-100',
    #     }))
    shipping_country = forms.ChoiceField(choices=[("US", "USA")])
    shipping_zip = forms.CharField(required=False)

    # name = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_city = forms.CharField(required=False)
    billing_state = forms.CharField(widget=USStateSelect(attrs={
        'class': 'custom-select d-block w-100',
    }))
    # billing_country = CountryField(blank_label='(select country)').formfield(
    #     required=False,
    #     widget=CountrySelectWidget(attrs={
    #         'class': 'custom-select d-block w-100',
    #     }))
    billing_country = forms.ChoiceField(choices=[("US", "USA")])
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    # set_default_shipping = forms.BooleanField(required=False)
    # use_default_shipping = forms.BooleanField(required=False)
    # set_default_billing = forms.BooleanField(required=False)
    # use_default_billing = forms.BooleanField(required=False)

    # payment_option = forms.ChoiceField(
    #     widget=forms.RadioSelect, choices=PAYMENT_CHOICES)

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo Code',
        'aria-label': "Recipient's username",
        'aria-describedby': "basic-addon2"
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()

# class AddToOrderForm(forms.Form):
#     quantity = forms.CharField(label="quantity", max_length=2)
#     variant_id =

class MailingListForm(forms.Form):
    first_name = forms.CharField()
    email_address = forms.EmailField()
