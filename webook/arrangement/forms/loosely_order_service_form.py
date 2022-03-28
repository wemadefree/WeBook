from django import forms
from webook.arrangement.models import LooseServiceRequisition, ServiceType, Event

class LooselyOrderServiceForm (forms.Form):
    events = forms.CharField()
    comment = forms.CharField()
    service_type = forms.IntegerField()

    def save(self):
        requisition = LooseServiceRequisition()
        requisition.comment = self.cleaned_data["comment"]
        requisition.type_to_order = ServiceType.objects.get(pk=self.cleaned_data["service_type"]) if self.cleaned_data["service_type"] is not None else None
        event_ids = self.cleaned_data["events"].split(",") if self.cleaned_data["events"] is not None else []
        requisition.arrangement = Event.objects.get(id=event_ids[0]).arrangement
        requisition.save()
        requisition.events.set(event_ids)

        requisition.save()

        

