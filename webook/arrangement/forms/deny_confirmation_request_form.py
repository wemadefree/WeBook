from django import forms
from webook.arrangement.models import ConfirmationReceipt
from webook.arrangement.facilities.confirmation_request import confirmation_request_facility

class DenyConfirmationRequestForm (forms.Form):
    token = forms.CharField()
    reasoning = forms.CharField()

    def perform_denial(self, confirmation_receipt:ConfirmationReceipt):
        confirmation_request_facility.deny_request(
            code=confirmation_receipt.code, 
            denial_reason=self.cleaned_data["reasoning"])
