from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=255)
    address = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=15)
    email = forms.EmailField()
    website = forms.URLField(required=False)
    bank_name = forms.CharField(max_length=255)
    bank_account = forms.CharField(max_length=20)
