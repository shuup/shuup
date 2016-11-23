# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail.message import EmailMessage
from django.db.models import Q
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _

from shuup.core.models import get_person_contact


class EmailAuthenticationForm(AuthenticationForm):

    error_messages = {
        'invalid_login': _("Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive. "
                           "In case of multiple accounts with same email only username can be used to login."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = _("Username or email address")

    def clean_username(self):
        username = self.cleaned_data['username']
        user_model = get_user_model()

        # Note: Always search by username AND by email prevent timing attacks
        try:
            user_by_name = user_model._default_manager.get_by_natural_key(username)
        except ObjectDoesNotExist:
            user_by_name = None

        try:
            user_by_email = user_model._default_manager.get(email=username)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            user_by_email = None

        if not user_by_name and user_by_email:
            return getattr(user_by_email, user_model.USERNAME_FIELD)

        return username

    def confirm_login_allowed(self, user):
        """
        Do not let user with inactive person contact to login.
        """
        if not get_person_contact(user).is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        super(EmailAuthenticationForm, self).confirm_login_allowed(user)


class RecoverPasswordForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=254, required=False)
    email = forms.EmailField(label=_("Email"), max_length=254, required=False)
    token_generator = default_token_generator
    subject_template_name = "shuup/user/recover_password_mail_subject.jinja",
    email_template_name = "shuup/user/recover_password_mail_content.jinja"
    from_email = None

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

        context = {
            'site_name': getattr(self.request, "shop", _("shop")),
            'uid': urlsafe_base64_encode(force_bytes(user_to_recover.pk)),
            'user_to_recover': user_to_recover,
            'token': self.token_generator.make_token(user_to_recover),
            'request': self.request,
        }
        subject = loader.render_to_string(self.subject_template_name, context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        body = loader.render_to_string(self.email_template_name, context, request=self.request)
        email = EmailMessage(from_email=self.from_email, subject=subject, body=body, to=[user_to_recover.email])
        email.content_subtype = settings.SHUUP_AUTH_EMAIL_CONTENT_SUBTYPE
        email.send()
        return True
