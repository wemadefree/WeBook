import datetime
from re import template
from django.urls import reverse
import string
from webook.arrangement.models import ConfirmationReceipt, Person
from enum import Enum
from django.core.mail import send_mail, EmailMessage
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
import secrets
import uuid
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist


_FAIL_SILENTLY=False

class InvalidRequestCodeException(Exception):
    """ Raised when an invalid request code is supplied """
    # TODO: Consider the need of logging invalid code redemptions. This is the best place to do so.
    pass


class MailMessageFactory():
    class ROUTINES(Enum):
        NOTIFY_REQUEST_MADE=1
        NOTIFY_REQUEST_CANCELLED=2
        NOTIFY_REQUEST_CONFIRMED=3
        NOTIFY_REQUEST_DENIED=4

    class BaseContextFabricator():
        def fabricate(self, confirmation_receipt):
            return {
                "ORIGINATOR_FRIENDLY_NAME": settings.APP_TITLE,
                "recipient": confirmation_receipt.sent_to,
                # "URL": 'https://' + Site.objects.get_current().domain + (reverse("arrangement:view_confirmation_request") + "?token=" + confirmation_receipt.code)
                "URL": 'http://127.0.0.1:8000' + (reverse("arrangement:view_confirmation_request") + "?token=" + confirmation_receipt.code)
            }

    def fabricate_email_message(self, routine: ROUTINES, confirmation_receipt: ConfirmationReceipt):
        mail_message = EmailMessage()
        fabrication_routine_options_dict = self._get_fabrication_strategy_map()[routine]
        
        mail_message.to = [confirmation_receipt.sent_to]
        mail_message.subject = fabrication_routine_options_dict["subject"]
        mail_message.body = self._generate_mailbody_from_template(
            template=fabrication_routine_options_dict["template"],
            context=fabrication_routine_options_dict["context_builder"](confirmation_receipt)
        )

        return mail_message

    def _get_fabrication_strategy_map(self):
        """ 
            Get the fabrication strategy map, providing routine-specific information necessary
            for tailored fabrications
        """
        return {
            self.ROUTINES.NOTIFY_REQUEST_MADE: { 
                "template": "mailing/confirmation_request/notify_request_made.html",
                "subject": _("Request of confirmation"),
                "context_builder": self.BaseContextFabricator().fabricate,
                },
            self.ROUTINES.NOTIFY_REQUEST_CANCELLED: {
                "template": "mailing/confirmation_request/notify_request_cancelled.html",
                "subject": _("Request cancelled"),
                "context_builder": self.BaseContextFabricator().fabricate,
            },
            self.ROUTINES.NOTIFY_REQUEST_DENIED: {
                "template": "mailing/confirmation_request/request_denied_receipt.html",
                "subject": _("Request denial receipt"),
                "context_builder": self.BaseContextFabricator().fabricate,
            },
            self.ROUTINES.NOTIFY_REQUEST_CONFIRMED: {
                "template": "mailing/confirmation_request/request_confirmed_receipt.html",
                "subject": _("Request confirmation receipt"),
                "context_builder": self.BaseContextFabricator().fabricate,
            },
        }

    def _generate_mailbody_from_template(self, template, context):
        """ 
            Generate the body of the mail using the given template
        """
        return render_to_string(template, context)


def _validate_request_obj(request:ConfirmationReceipt):
    if (request is None):
        raise InvalidRequestCodeException()

def is_request_token_valid(token:str):
    if not token: 
        return False

    try: 
        if ConfirmationReceipt.objects.get(code=token) is None: 
            return False
    except ObjectDoesNotExist:
        return False

    return True


def make_request (recipient_email: str, requested_by: Person, request_type, requisition_record):
    """
        Make a new confirmation request

        Returns a tuple, where;
            T1: bool indicating if mail send was success
            T2: created confirmationreceipt
    """
    request = ConfirmationReceipt()
    request.code = secrets.token_urlsafe(120)
    request.sent_to = recipient_email
    request.sent_when = datetime.datetime.now;
    request.requested_by = requested_by
    request.type = request_type
    request.save()
    
    requisition_record.confirmation_receipt = request
    requisition_record.save()

    print(requisition_record)
    print(request.requisition_record)

    requisition_record.get_requisition_data().on_made()

    email_message = MailMessageFactory().fabricate_email_message(
        routine=MailMessageFactory.ROUTINES.NOTIFY_REQUEST_MADE,
        confirmation_receipt=request,
    )

    return (bool(email_message.send(fail_silently=_FAIL_SILENTLY)), request)


def cancel_request(code:str):
    """
        Cancel a confirmation request

        Returns a tuple, where;
            T1: bool indicating if mail send was success
            T2: created confirmationreceipt
    """
    request = ConfirmationReceipt.objects.get(code=code)
    _validate_request_obj(request)

    request.state = ConfirmationReceipt.CANCELLED
    request.save()

    request.requisition_record.first().get_requisition_data().on_cancelled()

    email_message = MailMessageFactory().fabricate_email_message(
        routine=MailMessageFactory.ROUTINES.NOTIFY_REQUEST_CANCELLED,
        confirmation_receipt=request
    )
    return (bool(email_message.send(fail_silently=_FAIL_SILENTLY)), request)


def deny_request(code:str, denial_reason:str=None):
    """ 
        Deny a confirmation request
        
        Returns a tuple, where;
            T1: bool indicating if mail send was success
            T2: created confirmationreceipt
    """
    request = ConfirmationReceipt.objects.get(code=code)
    _validate_request_obj(request)

    request.state = ConfirmationReceipt.DENIED
    if (denial_reason):
        request.denial_reasoning = denial_reason
    request.save()

    request.requisition_record.first().get_requisition_data().on_denied()

    email_message = MailMessageFactory().fabricate_email_message(
        routine=MailMessageFactory.ROUTINES.NOTIFY_REQUEST_DENIED,
        confirmation_receipt=request
    )
    return (bool(email_message.send(fail_silently=_FAIL_SILENTLY)), request)


def confirm_request(code:str):
    """
        Confirm a confirmation request
        
        Returns a tuple, where;
            T1: bool indicating if mail send was success
            T2: created confirmationreceipt
    """
    request = ConfirmationReceipt.objects.get(code=code)
    _validate_request_obj(request)

    request.state = ConfirmationReceipt.CONFIRMED
    request.save()

    request.requisition_record.first().get_requisition_data().on_confirm()

    email_message = MailMessageFactory().fabricate_email_message(
        routine=MailMessageFactory.ROUTINES.NOTIFY_REQUEST_CONFIRMED,
        confirmation_receipt=request
    )
    return (bool(email_message.send(fail_silently=_FAIL_SILENTLY)), request)