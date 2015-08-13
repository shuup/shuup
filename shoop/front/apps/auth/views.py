# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import REDIRECT_FIELD_NAME
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext as _
from django.views.generic import FormView, TemplateView

from shoop.utils.excs import Problem


class LoginView(FormView):
    template_name = 'shoop/user/login.jinja'
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        url = self.request.REQUEST.get(REDIRECT_FIELD_NAME)
        if url and is_safe_url(url, self.request.get_host()):
            return url
        return settings.LOGIN_REDIRECT_URL


class LogoutView(TemplateView):
    template_name = "shoop/user/logout.jinja"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            logout(request)
        return super(LogoutView, self).dispatch(request, *args, **kwargs)


class RecoverPasswordForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)
    token_generator = default_token_generator
    subject_template_name = "shoop/user/recover_password_mail_subject.jinja",
    email_template_name = "shoop/user/recover_password_mail_content.jinja"
    from_email = None

    def save(self, request):
        self.request = request
        user_model = get_user_model()
        active_users = user_model.objects.filter(email__iexact=self.cleaned_data["email"], is_active=True)
        for user in active_users:
            self.process_user(user)

    def process_user(self, user):
        if not user.has_usable_password():
            return False

        context = {
            'email': user.email,
            'site_name': getattr(self.request, "shop", _("shop")),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': self.token_generator.make_token(user),
            'request': self.request,
        }
        subject = loader.render_to_string(self.subject_template_name, context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        email = loader.render_to_string(self.email_template_name, context, request=self.request)
        send_mail(subject, email, self.from_email, [user.email])
        return True


class RecoverPasswordView(FormView):
    template_name = "shoop/user/recover_password.jinja"
    form_class = RecoverPasswordForm
    success_url = reverse_lazy("shoop:recover_password_sent")

    def form_valid(self, form):
        """
        :type form: RecoverPasswordForm
        """
        form.save(request=self.request)
        return HttpResponseRedirect(self.get_success_url())


class RecoverPasswordConfirmView(FormView):
    template_name = "shoop/user/recover_password_confirm.jinja"
    form_class = SetPasswordForm
    token_generator = default_token_generator
    success_url = reverse_lazy("shoop:recover_password_complete")

    def get_form_kwargs(self):
        kwargs = super(RecoverPasswordConfirmView, self).get_form_kwargs()
        kwargs["user"] = self.get_target_user()
        return kwargs

    def get_target_user(self):
        uidb64 = self.kwargs["uidb64"]
        user_model = get_user_model()
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = user_model._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            user = None
        return user

    def dispatch(self, request, *args, **kwargs):
        user = self.get_target_user()
        token = self.kwargs["token"]

        valid = (user is not None and self.token_generator.check_token(user, token))
        if not valid:
            raise Problem(_(u"This recovery link is invalid."))

        return super(RecoverPasswordConfirmView, self).dispatch(request, *args, **kwargs)

    @atomic
    def form_valid(self, form):
        """
        :type form: SetPasswordForm
        """
        form.save()
        form.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, form.user)
        return HttpResponseRedirect(self.get_success_url())


class RecoverPasswordSentView(TemplateView):
    template_name = "shoop/user/recover_password_sent.jinja"


class RecoverPasswordCompleteView(TemplateView):
    template_name = "shoop/user/recover_password_complete.jinja"
