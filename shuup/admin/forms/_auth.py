# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.utils.forms import RecoverPasswordForm


class EmailAuthenticationForm(AuthenticationForm):

    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. "
            "Note that both fields may be case-sensitive. "
            "In case of multiple accounts with the same email, only username can be used to log in."
        ),
        "inactive": _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields["username"].label = _("Username or email address")

    def clean_username(self):
        username = self.data["username"]
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

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(request=self.request, username=username, password=password)

            # So here even with invalid login and user cache being None
            # we want to check whether the user we are trying to
            # log in is inactive or not.
            try:
                user_temp = get_user_model().objects.get(username=username)
            except ObjectDoesNotExist:
                user_temp = None

            if user_temp is not None:
                self.confirm_login_allowed(user_temp)

            # Back to default behavior. Meaning that we want to always
            # raise for invalid login in case the authenticate fails.
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )


class RequestPasswordForm(RecoverPasswordForm):
    token_generator = default_token_generator
    subject_template_name = "shuup/admin/auth/recover_password_mail_subject.jinja"
    email_template_name = "shuup/admin/auth/recover_password_mail_content.jinja"
    from_email = None
    recover_password_confirm_view_url_name = "shuup_admin:recover_password"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(RequestPasswordForm, self).__init__(*args, **kwargs)

    def save(self):
        user_model = get_user_model()
        username = self.cleaned_data.get("username")
        email = self.cleaned_data.get("email")
        username_filter = {"{0}__iexact".format(user_model.USERNAME_FIELD): username}
        # only staff and active users
        # only staff ( Access to Admin Panel ) and active users
        active_users = user_model.objects.filter(
            Q(is_active=True, is_staff=True),
            Q(**username_filter) | Q(email__iexact=email),
        )
        for user in active_users:
            self.process_user(user, self.request)
