from django import forms
from django.forms import ModelForm, ChoiceField, RadioSelect

from django_snippets.empty_choice_field import EmptyChoiceField

from .models import Contact, Deployment, Support, Info, Contribute


class Html5EmailInput(forms.TextInput):
    """adding email attributes"""
    input_type = 'email'


class ContactForm(ModelForm):
    required_css_class = 'required'
    ip = forms.CharField(widget=forms.HiddenInput)
    type = EmptyChoiceField(choices=Contact.CONTACT_TYPES, label="Reason for Contact:", widget=forms.Select(attrs={ 'required': 'true' }))

    class Meta:
        model = Contact
        fields = ('name', 'email', 'org_name', 'type', "ip")
        widgets = {
            'name': forms.TextInput(attrs={ 'required': 'true' }),
            'email': Html5EmailInput(attrs={ 'required': 'true' }),
        }


class DeploymentForm(ModelForm):
    required_css_class = 'required'
    class Meta:
        model = Deployment
        fields = ('organization', 'countries', 'internet_access', 'hardware_infrastructure', 'facilities', 'other' )
        widgets = {
            'organization': forms.TextInput(attrs={ 'required': 'false', 'style': 'width: 550px;' }),
        }

class SupportForm(ModelForm):
    required_css_class = 'required'
    type = EmptyChoiceField(choices=Support.SUPPORT_TYPES, label="Issue Type:")
    class Meta:
        model = Support
        fields = ('type', 'issue')

class InfoForm(ModelForm):
    required_css_class = 'required'
    class Meta:
        model = Info
        fields = ('issue',)

class ContributeForm(ModelForm):
    type = EmptyChoiceField(choices=Support.SUPPORT_TYPES, label="Type of contribution:")
    required_css_class = 'required'
    class Meta:
        model = Contribute
        fields = ('type','issue',)

