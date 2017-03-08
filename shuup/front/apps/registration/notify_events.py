# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from registration.signals import user_registered

from shuup.core.models import CompanyContact, PersonContact
from shuup.notify.base import Event, Variable
from shuup.notify.script_template.factory import \
    generic_send_email_script_template_factory
from shuup.notify.typology import Email


class RegistrationReceivedEvent(Event):
    customer_email = Variable(_("Customer Email"), type=Email)


class RegistrationReceived(RegistrationReceivedEvent):
    identifier = "registration_received"
    name = _("Registration Received")


class CompanyRegistrationReceived(RegistrationReceivedEvent):
    identifier = "company_registration_received"
    name = _("Company Registration Received")


@receiver(user_registered)
def send_user_registered_notification(user, **kwargs):
    person_contact = PersonContact.objects.filter(user=user).first()
    cls = RegistrationReceived
    if person_contact:
        if CompanyContact.objects.filter(members__in=[user.email]).exists():
            cls = CompanyRegistrationReceived
    cls(customer_email=user.email).run()


RegistrationReceivedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="registration_received_email",
    event=RegistrationReceived,
    name=_("Send Registration Received Email"),
    description=_("Send email when a user registers."),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a user get registered."),
    initial=dict(
        subject=_("{{ order.shop }} - Welcome!")
    )
)

CompanyRegistrationReceivedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="company_registration_received_email",
    event=CompanyRegistrationReceived,
    name=_("Send Registration Received Email"),
    description=_("Send email when a user registers."),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a user get registered."),
    initial=dict(
        subject=_("{{ order.shop }} - Welcome!")
    )
)
