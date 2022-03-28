from django import forms
from webook.arrangement.models import Arrangement, LooseServiceRequisition


class ResetRequisitionForm(forms.Form):
    loose_service_requisition_id = forms.IntegerField()

    def reset(self):
        loose_service_requisition =  LooseServiceRequisition.objects.get(id=self.cleaned_data["loose_service_requisition_id"])
        requisition_record = loose_service_requisition.generated_requisition_record
        actual_requisition = loose_service_requisition.actual_requisition

        actual_requisition.originating_loose_requisition = None
        loose_service_requisition.generated_requisition_record = None
        loose_service_requisition.save()
        

        # requisition_record.delete()
        # actual_requisition.delete()

        loose_service_requisition.save()
