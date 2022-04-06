from django import forms
from webook.arrangement.models import LooseServiceRequisition
from webook.arrangement.facilities.confirmation_request import confirmation_request_facility


class CancelServiceRequisitionForm(forms.Form):
    loose_service_requisition_id = forms.IntegerField()

    def cancel_service_requisition(self):
        loose_service_requisition =  LooseServiceRequisition.objects.get(id=self.cleaned_data["loose_service_requisition_id"])
        
        confirmation_request_facility.cancel_request(
            code=loose_service_requisition.generated_requisition_record.confirmation_receipt.code
        )
