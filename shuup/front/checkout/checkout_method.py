# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from registration.signals import login_user

from shuup.front.apps.auth.views import LoginView
from shuup.front.apps.registration.views import (
    RegistrationNoActivationView, RegistrationWithActivationView, RegistrationView
)
from shuup.front.checkout import CheckoutPhaseViewMixin
from shuup.utils.form_group import FormGroup

CHECKOUT_CHOICE_STORAGE_KEY = "checkout_method:checkout_method_choice"


class CheckoutMethodChoices(Enum):
    CHECKOUT_AS_GUEST = 0
    REGISTER = 1

    class Labels:
        CHECKOUT_AS_GUEST = _("Checkout as Guest")
        REGISTER = _("Register")


class ChooseToRegisterForm(forms.Form):
    register = forms.ChoiceField(
        choices=CheckoutMethodChoices.choices(), initial=CheckoutMethodChoices.REGISTER.value,
        label=_("Register with us for future convenience"), required=False
    )


class CheckoutMethodPhase(CheckoutPhaseViewMixin, LoginView):
    identifier = "checkout_method"
    title = _("Checkout Method Choice")
    template_name = "shuup/front/checkout/checkout_method.jinja"
    login_form_key = "login"
    checkout_method_choice_key = "checkout_method_choice"

    def get_form(self, form_class=None):
        form_group = FormGroup(**self.get_initial_form_group_kwargs())
        form_group.add_form_def(name=self.login_form_key, form_class=LoginView.form_class, required=False,
                                kwargs={"request": self.request})
        form_group.add_form_def(name=self.checkout_method_choice_key, form_class=ChooseToRegisterForm, required=False)
        return form_group

    def is_visible_for_user(self):
        return bool(not self.request.customer or self.request.customer.is_all_seeing)

    def should_skip(self):
        return not self.is_visible_for_user()

    def is_valid(self):
        checkout_method_choice = bool(self.storage.get(CHECKOUT_CHOICE_STORAGE_KEY, None) is not None)
        return bool(checkout_method_choice or self.request.customer)

    def form_valid(self, form):
        login_form = form.forms[self.login_form_key]
        if login_form.cleaned_data:  # TODO: There is probably better way to figure out when to login
            return super(CheckoutMethodPhase, self).form_valid(login_form)
        checkout_choice_form = form.forms[self.checkout_method_choice_key]
        should_register = bool(int(checkout_choice_form.cleaned_data["register"] or 0))
        self.storage[CHECKOUT_CHOICE_STORAGE_KEY] = should_register
        self.request.session["checkout_register:%s" % CHECKOUT_CHOICE_STORAGE_KEY] = should_register
        return HttpResponseRedirect(self.get_success_url())

    def process(self):
        return

    def get_initial_form_group_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form group.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs


class RegisterPhaseMixin:
    identifier = "register"
    title = _("Register")
    template_name = "shuup/front/checkout/register.jinja"

    def is_visible_for_user(self):
        checkout_method_choice_is_registered = bool(self.storage.get(CHECKOUT_CHOICE_STORAGE_KEY, None))
        return bool(not self.request.customer and checkout_method_choice_is_registered)

    def should_skip(self):
        return not self.is_visible_for_user()

    def is_valid(self):
        checkout_method_choice_is_registered = bool(self.storage.get(CHECKOUT_CHOICE_STORAGE_KEY, None))
        return bool(self.request.customer and checkout_method_choice_is_registered)

    def process(self):
        return


class RegisterPhase(RegisterPhaseMixin, CheckoutPhaseViewMixin, RegistrationNoActivationView):
    pass


class RegisterWithActivationPhase(RegisterPhaseMixin, CheckoutPhaseViewMixin, RegistrationView):
    """Registration with mandatory activation over email.

    Blocks further checkout process until user activates their account
    by clicking the activation link in the email.
    """
    pass


class RegisterWithDeferredActivationPhase(RegisterPhaseMixin, CheckoutPhaseViewMixin, RegistrationWithActivationView):
    """Registration with activation over email, but also automatically
    logging in the (still inactive) user, thus not creating an
    interruption in the checkout process. This assumes that the
    `AllowAllUsersModelBackend` auth backend is used for
    authentication (i.e. django allows inactive users to login).
    """
    def add_activation_message(self):
        """Add a message notifying the user that their acount is inactive."""
        messages.success(
            self.request,
            _(
                "Thank you for registering. You can activate your account "
                "later by clicking the activation link we have just sent you."
            ),
            extra_tags="registered-activate-later",
        )

    def register(self, form):
        user = super().register(form)
        login_user(self, user, self.request)
        self.add_activation_message()
        return user
