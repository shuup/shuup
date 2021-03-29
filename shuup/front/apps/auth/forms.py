# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.translation import ugettext as _

from shuup.apps.provides import get_provide_objects
from shuup.core.models import get_person_contact
from shuup.front.signals import login_allowed


class EmailAuthenticationForm(AuthenticationForm):

    error_messages = {
        "invalid_login": _(
            "Error! Please enter a correct %(username)s and password. "
            "Note that both fields may be case-sensitive. "
            "In case of multiple accounts with same email only username can be used to log in."
        ),
        "inactive": _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields["username"].label = _("Username or email address")
        for provider_cls in get_provide_objects("front_auth_form_field_provider"):
            provider = provider_cls()
            for definition in provider.get_fields(request=self.request):
                self.fields[definition.name] = definition.field

    def clean_username(self):
        username = self.cleaned_data["username"]
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
            # login is inactive or not.
            try:
                user_temp = get_user_model().objects.get(username=username)
            except ObjectDoesNotExist:
                user_temp = None

            if user_temp is not None:
                self.confirm_login_allowed(user_temp)

            # Back to default behavior. Meaning that we want to always
            # raise for invalid login incase the authenticate failed
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )

    def confirm_login_allowed(self, user):
        """
        Do not let inactive person contact user to login.
        """
        if not get_person_contact(user).is_active:
            raise forms.ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP:
            if not user.is_superuser:
                shop = self.request.shop
                if shop not in user.contact.shops.all():
                    raise forms.ValidationError(_("You are not allowed to log in to this shop."))

        super(EmailAuthenticationForm, self).confirm_login_allowed(user)

        login_allowed.send(sender=type(self), request=self.request, user=user)
