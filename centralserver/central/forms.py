from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext as _

from .models import Organization, OrganizationInvitation
from securesync.devices.models import Zone
from kalite.facility.models import Facility, FacilityGroup
from centralserver.central.models import ExportJob


class OrganizationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'description', 'url', 'number', 'address', 'country')


class OrganizationInvitationForm(ModelForm):
    class Meta:
        model = OrganizationInvitation
        fields = ('email_to_invite', 'invited_by', 'organization')
        widgets = {
            'invited_by': forms.HiddenInput(),
            'organization': forms.HiddenInput(),
        }

    def clean(self):
        email_to_invite = self.cleaned_data.get('email_to_invite')
        organization = self.cleaned_data.get('organization')
        user = self.cleaned_data.get('invited_by')

        if not email_to_invite:
            raise forms.ValidationError(_("The email address you entered is invalid."))
        if email_to_invite == user.email:
            raise forms.ValidationError(_("You are already a part of this organization."))
        if OrganizationInvitation.objects.filter(organization=organization, email_to_invite=email_to_invite).count() > 0:
            raise forms.ValidationError(_("You have already sent an invitation email to this user."))

        return self.cleaned_data


class ExportForm(forms.ModelForm):
    
    # This field is used to control whether the form is submitted or we just
    # had a .change() event on one of the Select widgets.
    submitted = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    
    # The QuerySet objects are filled once the form is instantiated
    zone = forms.ModelChoiceField(Zone.objects.none(), required=False)
    facility = forms.ModelChoiceField(Facility.objects.none(), required=False)
    facility_group = forms.ModelChoiceField(FacilityGroup.objects.none(), required=False)
    
    resource = forms.ChoiceField(
        choices=[
            ('user_logs', "User logs"),
            ('attempt_logs', "Attempt logs"),
            ('exercise_logs', "Exercise logs"),
            ('ratings', "Ratings"),
            ('device_logs', "Device logs"),
        ],
        required=True
    )
    
    def __init__(self, organization, *args, **kwargs):
        self.organization = organization
        super(ExportForm, self).__init__(*args, **kwargs)
        self.fields['zone'].queryset = self.organization.zones
        data = self.data
        if 'zone' in data:
            self.fields['facility'].queryset = Facility.objects.by_zone(
                data.get('zone', 0)
            )
        if 'facility' in data:
            self.fields['facility_group'].queryset = FacilityGroup.objects.filter(
                facility__id=data.get('facility', 0)
            ).distinct()

    def save(self, *args, **kwargs):
        job = super(ExportForm, self).save(commit=False)
        job.organization = self.organization
        job.save()
        return job

    class Meta:
        model = ExportJob
        fields = ('zone', 'facility', 'facility_group', 'resource')
