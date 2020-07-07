# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail.message import EmailMessage
from django.db.models import Q
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Contact, ImmutableAddress, MutableAddress
from shuup.utils.django_compat import reverse
from shuup.utils.djangoenv import has_installed
from shuup.utils.iterables import first


class MutableAddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "name", "name_ext", "phone", "email",
            "street", "street2", "postal_code", "city",
            "region", "region_code", "country"
        )
        labels = {
            "region_code": _("Region")
        }

    def __init__(self, **kwargs):
        super(MutableAddressForm, self).__init__(**kwargs)
        if not kwargs.get("instance"):
            # Set default country
            self.fields["country"].initial = settings.SHUUP_ADDRESS_HOME_COUNTRY

        field_properties = settings.SHUUP_ADDRESS_FIELD_PROPERTIES
        for field, properties in field_properties.items():
            for prop in properties:
                setattr(self.fields[field], prop, properties[prop])

    def save(self, commit=True):
        if self.instance.pk:
            if isinstance(self.instance, ImmutableAddress) or _is_assigned_multiple_times(self.instance):
                self.instance.pk = None  # Force resave
        return super(MutableAddressForm, self).save(commit)


def _is_assigned_multiple_times(address):
    contacts_assigned_to_count = Contact.objects.filter(
        Q(default_billing_address_id=address.id) | Q(default_shipping_address_id=address.id)).count()
    if contacts_assigned_to_count != 1:
        return bool(contacts_assigned_to_count)
    contact_assigned_to = Contact.objects.filter(
        Q(default_billing_address_id=address.id) | Q(default_shipping_address_id=address.id)).first()
    return bool(contact_assigned_to.default_billing_address_id == contact_assigned_to.default_shipping_address_id)


class FormInfoMap(OrderedDict):
    def __init__(self, form_classes):
        form_infos = (FormInfo(formcls) for formcls in form_classes)
        super(FormInfoMap, self).__init__(
            (form_info.choice_value, form_info) for form_info in form_infos)

    def get_by_object(self, obj):
        return first(
            form_info for form_info in self.values() if isinstance(obj, form_info.model))

    def get_by_choice_value(self, choice_value):
        return self.get(choice_value)

    def get_type_choices(self):
        return [(x.choice_value, x.choice_text) for x in self.values()]


class FormInfo(object):
    def __init__(self, form_class):
        self.form_class = form_class
        self.model = form_class._meta.model
        model_meta = self.model._meta
        self.choice_value = model_meta.app_label + '.' + model_meta.model_name
        self.choice_text = model_meta.verbose_name.capitalize()


class RecoverPasswordForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=254, required=False)
    email = forms.EmailField(label=_("Email"), max_length=254, required=False)
    token_generator = default_token_generator
    subject_template_name = "shuup/user/recover_password_mail_subject.jinja"
    email_template_name = "shuup/user/recover_password_mail_content.jinja"
    from_email = None
    recover_password_confirm_view_url_name = "shuup:recover_password_confirm"

    def clean(self):
        data = self.cleaned_data
        username = data.get("username")
        email = data.get("email")
        if username and email:
            msg = _("Please provide either username or email, not both.")
            self.add_error("username", msg)
            self.add_error("email", msg)

        if not (username or email):
            msg = _("Please provide either username or email.")
            self.add_error("username", msg)
            self.add_error("email", msg)

        return data

    def save(self, request):
        self.request = request
        user_model = get_user_model()

        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]

        username_filter = {"{0}__iexact".format(user_model.USERNAME_FIELD): username}

        active_users = user_model.objects.filter(
            Q(**username_filter) | Q(email__iexact=email), Q(is_active=True)
        )

        for user in active_users:
            self.process_user(user)

    def process_user(self, user_to_recover):
        if (not user_to_recover.has_usable_password() or
           not hasattr(user_to_recover, 'email') or
           not user_to_recover.email):
            return False

        uid = urlsafe_base64_encode(force_bytes(user_to_recover.pk))
        token = self.token_generator.make_token(user_to_recover)
        context = {
            'site_name': getattr(self.request, "shop", _("shop")),
            'uid': uid,
            'user_to_recover': user_to_recover,
            'token': token,
        }

        notification_sent = False
        request = getattr(self, "request", None)
        if has_installed('shuup.notify') and request and request.shop and self.recover_password_confirm_view_url_name:
            # Send notification event if any Script enabled
            from shuup.notify.models import Script
            from shuup.notify.notify_events import PasswordReset
            if Script.objects.filter(enabled=True, event_identifier=PasswordReset.identifier).exists():
                notification_sent = True
                recovery_url = request.build_absolute_uri(
                    reverse(self.recover_password_confirm_view_url_name, kwargs=dict(uidb64=uid, token=token))
                )
                context.update({'customer_email': user_to_recover.email, 'recovery_url': recovery_url})
                try:
                    PasswordReset(**context).run(shop=self.request.shop)
                    notification_sent = True
                except Exception:
                    notification_sent = False

        if not notification_sent:
            context.update({'request': self.request})
            subject = loader.render_to_string(self.subject_template_name, context)
            subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
            body = loader.render_to_string(self.email_template_name, context, request=self.request)
            email = EmailMessage(from_email=self.from_email, subject=subject, body=body, to=[user_to_recover.email])
            email.content_subtype = settings.SHUUP_AUTH_EMAIL_CONTENT_SUBTYPE
            email.send()
        return True
