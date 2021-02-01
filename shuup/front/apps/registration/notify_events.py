# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from registration.signals import user_activated, user_registered

from shuup.core.models import get_person_contact, PersonContact
from shuup.notify.base import Event, Variable
from shuup.notify.script_template.factory import (
    generic_send_email_script_template_factory
)
from shuup.notify.typology import Boolean, Email, Model, URL
from shuup.utils.django_compat import reverse

from .signals import user_reactivated


class RegistrationReceived(Event):
    identifier = "registration_received"
    name = _("Registration Received")
    customer = Variable(_("Customer"), type=Model("shuup.Contact"))
    customer_email = Variable(_("Customer Email"), type=Email)
    activation_url = Variable(_("Activation URL"), type=URL, required=False)
    user_is_active = Variable(_("Is User Active"), type=Boolean)


class AccountReactivation(RegistrationReceived):
    identifier = "account_reactivation"
    name = _("Account Reactivation")


class CompanyRegistrationReceived(RegistrationReceived):
    identifier = "company_registration_received"
    name = _("Company Registration Received")


class CompanyApproved(RegistrationReceived):
    identifier = "company_approved_by_admin"
    name = _("Company Approved")


class AccountActivation(RegistrationReceived):
    identifier = "account_activation"
    name = _("Account Activation")


@receiver(user_activated)
def send_activation_notification(user, request, **kwargs):
    cls = AccountActivation
    customer = get_person_contact(user)
    email = user.email
    event = cls(
        customer=customer,
        customer_email=email,
        user_is_active=user.is_active,
    )
    event.run(shop=request.shop)


@receiver(user_registered)
def send_user_registered_notification(user, request, **kwargs):
    activation_url = None
    person_contact = get_person_contact(user)
    activation_key = user.registrationprofile.activation_key if hasattr(user, 'registrationprofile') else None
    if activation_key:
        activation_path = reverse('shuup:registration_activate', args=(activation_key,))
        activation_url = request.build_absolute_uri(activation_path)

    customer = person_contact
    cls = RegistrationReceived
    email = user.email

    if person_contact:
        company = person_contact.company_memberships.first()
        if company:
            customer = company
            cls = CompanyRegistrationReceived
            email = user.email or company.email
    event = cls(
        customer=customer,
        customer_email=email,
        activation_url=activation_url,
        user_is_active=user.is_active,
    )
    event.run(shop=request.shop)


@receiver(user_reactivated)
def send_reactivation_notification(user, request, **kwargs):
    cls = AccountReactivation
    customer = get_person_contact(user)
    email = user.email

    event = cls(
        customer=customer,
        customer_email=email,
        user_is_active=user.is_active,
    )
    event.run(shop=request.shop)


def send_company_activated_first_time_notification(instance, request, **kwargs):
    activated_once = instance.log_entries.filter(identifier='company_activated').exists()
    if activated_once or not instance.is_active:
        return
    # Send email if a company was never activated before
    instance.add_log_entry(
        message=_("Company has been activated."),
        identifier='company_activated'
    )
    person = instance.members.instance_of(PersonContact).first()
    user = person.user

    activation_url = None
    activation_key = user.registrationprofile.activation_key if hasattr(user, 'registrationprofile') else None
    if activation_key:
        activation_path = reverse('shuup:registration_activate', args=(activation_key,))
        activation_url = request.build_absolute_uri(activation_path)

    email = user.email or instance.email
    customer = instance
    event = CompanyApproved(
        customer=customer,
        customer_email=email,
        user_is_active=user.is_active,
        activation_url=activation_url
    )
    event.run(shop=request.shop)


RegistrationReceivedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="registration_received_email",
    event=RegistrationReceived,
    name=_("Send Registration Received Email"),
    description=_("Send email when a user registers."),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a user get registered."),
    initial={
        "en-subject": _("{{ order.shop }} - Welcome!")
    }
)

AccountReactivationEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="account_reactivated",
    event=AccountReactivation,
    name=_("Send account reactivation email"),
    description=_("Send email when a user account gets reactivated"),
    help_text=_(
        "This script will send an email to the user or to any configured email "
        "when a account get's reactivated"
    ),
    initial={
        "en-subject": _("{{ customer.username }} is now active again!")
    }
)

CompanyRegistrationReceivedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="company_registration_received_email",
    event=CompanyRegistrationReceived,
    name=_("Send Company Registration Received Email"),
    description=_("Send email when a user registers as a company."),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a user get registered."),
    initial={
        "en-subject": _("{{ order.shop }} - Welcome!")
    }
)

CompanyActivatedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="company_activated_email",
    event=CompanyApproved,
    name=_("Send Company Activated Email"),
    description=_("Notify company's contact person that company account is activated"),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a company is activated."),
    initial={
        "en-subject": _("{{ order.shop }} - Welcome!")
    }
)


AccountActivationEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="account_reactivated",
    event=AccountActivation,
    name=_("Send account activation email"),
    description=_("Send email when a user account gets activated for the first time"),
    help_text=_(
        "This script will send an email to the user or to any configured email "
        "when an account gets activated for the first time"
    ),
    initial={
        "en-subject": _("{{ customer.username }} is now active!")
    }
)
