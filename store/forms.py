from typing import Type
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Address, Review
from cities_light.models import City, Region, SubRegion

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



