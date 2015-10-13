# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import send_mail
from django.db.models import Q
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _


class EmailAuthenticationForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = _("Username or email address")

    def clean_username(self):
        username = self.data['username']
        user_model = get_user_model()
        if '@' in username:
            try:
                username = user_model.objects.get(email=username).username
            except MultipleObjectsReturned:
                raise forms.ValidationError(
                    _("Multiple users have this email, please use username to login."),
                    code='invalid_login_multiple_users'
                )
        return username


class RecoverPasswordForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=254, required=False)
    email = forms.EmailField(label=_("Email"), max_length=254, required=False)
    token_generator = default_token_generator
    subject_template_name = "shoop/user/recover_password_mail_subject.jinja",
    email_template_name = "shoop/user/recover_password_mail_content.jinja"
    from_email = None

    def clean(self):
        data = self.cleaned_data
        if not (data["username"] or data["email"]):
            raise forms.ValidationError(
                _("Please provide either username or password"), code="no_email_or_username"
            )
        return data

    def save(self, request):
        self.request = request
        user_model = get_user_model()

        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        active_users = user_model.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=email), Q(is_active=True)
        )

        for user in active_users:
            self.process_user(user)

    def process_user(self, user_to_recover):
        if not user_to_recover.has_usable_password():
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
        email = loader.render_to_string(self.email_template_name, context, request=self.request)
        send_mail(subject, email, self.from_email, [user_to_recover.email])
        return True
