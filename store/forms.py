import re
from typing import Type
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Address, Refund, Review, Card
from cities_light.models import City, Region, SubRegion
from django.utils import timezone

class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.name

class ProductQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)


class ProductIDQuantityForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1)

class ContactForm(forms.Form):
	first_name = forms.CharField(max_length = 50)
	last_name = forms.CharField(max_length = 50)
	email_address = forms.EmailField(max_length = 150)
	message = forms.CharField(widget = forms.Textarea, max_length = 2000)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ( 'subject', 'comment', 'rating')

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ('reason',)

class CardForm(forms.ModelForm):
    name = forms.CharField(max_length=60, required=True)
    number = forms.CharField(max_length=20, required=True)
    cvc = forms.CharField(max_length=20, required=True)
    expiry = forms.CharField(max_length=15, required=True)

    class Meta:
        model = Card
        fields = ('name', 'number', 'cvc', 'expiry')

    def clean(self):
        cleaned_data = super().clean()
        number = cleaned_data.get('number')
        cvc = cleaned_data.get('cvc')
        expiry = cleaned_data.get('expiry')

        if number is None:
            self.add_error('number', "Correctly enter all numbers.")
        else:                        
            number_list = number.split(" ")
            if len(number_list) != 4:
                self.add_error('number', "Correctly enter all numbers.")
            else:
                for i in number_list:
                    if len(i) != 4:
                        self.add_error('number', "Correctly enter all numbers.")
        if cvc is None:
            self.add_error('cvc', "Correctly enter cvc.")
        elif len(cvc) < 3:
            self.add_error('cvc', "Correctly enter cvc.")
        if expiry is None:
            self.add_error('expiry', "Correctly enter expiry date.")
        else:
            now = timezone.now()
            month = now.month
            year = now.year
            expiry_list = expiry.split(" ")
            if len(expiry_list) < 3:
                self.add_error('expiry', "Correctly enter expiry date.") 
            else:           
                if year > int(expiry_list[2]):
                    self.add_error('expiry', "Your card is expired.")
                if year == int(expiry_list[2]) and month > int(expiry_list[0]):
                    self.add_error('expiry', "Your card is expired.")


        

class AddressForm(forms.ModelForm):
    name = forms.CharField(max_length=50, required=True)
    address = forms.CharField(max_length=400, required=True, widget=forms.Textarea(attrs={
        'rows': 3,
    }))
    region = UserModelChoiceField(queryset=Region.objects.all(), required=True, widget=forms.Select())
    subregion = UserModelChoiceField(queryset=SubRegion.objects.all(), required=True, widget=forms.Select())
    zip = forms.CharField(max_length=50, required=True)

    class Meta:
        model = Address
        fields = ( 'name', 'address' , 'region', 'subregion', 'zip')

    def _init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subregion'].queryset = SubRegion.objects.none()
        self.fields['address'].widget.attrs['rows'] = 2

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['subregion'].queryset = SubRegion.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subregion'].queryset = self.instance.region.subregion_set.order_by('name')



