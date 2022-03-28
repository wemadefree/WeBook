from django import forms
from webook.arrangement.models import ServiceProvidable, Organization, ServiceType


class RegisterServiceProvidableForm(forms.Form):
    organization_slug = forms.SlugField()
    service_type = forms.SlugField()
    contact_email = forms.EmailField()

    def save(self):
        organization = Organization.objects.get(slug=self.cleaned_data["organization_slug"])
        service_type = ServiceType.objects.get(id=self.cleaned_data["service_type"])

        service_providable_record = ServiceProvidable()
        service_providable_record.service_type = service_type
        service_providable_record.organization = organization
        service_providable_record.service_contact = self.cleaned_data["contact_email"]

        service_providable_record.save()