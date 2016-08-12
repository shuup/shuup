# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random

from django import forms
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model, load_backend, login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db.transaction import atomic
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView

from shuup.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownItem,
    get_default_edit_toolbar, PostActionButton, Toolbar
)
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Contact, PersonContact
from shuup.utils.excs import Problem
from shuup.utils.text import flatten


def get_front_url():
    front_url = None
    try:
        front_url = reverse("shuup:index")
    except NoReverseMatch:
        front_url = None
    return front_url


class BaseUserForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    permission_info = forms.CharField(
        label=_("Permissions"),
        widget=forms.TextInput(attrs={"readonly": True, "disabled": True}),
        required=False,
        help_text=_("See the permissions view to change these.")
    )
    permission_groups = forms.CharField(
        label=_("Permission Groups"),
        widget=forms.TextInput(attrs={"readonly": True, "disabled": True}),
        required=False,
        help_text=_("See the permissions view to change these.")
    )

    def __init__(self, *args, **kwargs):
        super(BaseUserForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            # Changing the password for an existing user requires more confirmation
            self.fields.pop("password")
            self.initial["permission_info"] = ", ".join(force_text(perm) for perm in [
                _("staff") if getattr(self.instance, 'is_staff', None) else "",
                _("superuser") if getattr(self.instance, 'is_superuser', None) else "",
            ] if perm) or _("No special permissions")
            if hasattr(self.instance, "groups"):
                group_names = [force_text(group) for group in self.instance.groups.all()]
                self.initial["permission_groups"] = ", ".join(sorted(group_names))
            else:
                self.initial["permission_groups"] = _("No permission groups")
        else:
            self.fields.pop("permission_info")
            self.fields.pop("permission_groups")

    def save(self, commit=True):
        user = super(BaseUserForm, self).save(commit=False)

        if "password" in self.fields:
            user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class UserDetailToolbar(Toolbar):
    def __init__(self, view):
        self.view = view
        self.request = view.request
        self.user = view.object
        super(UserDetailToolbar, self).__init__()
        self.extend(get_default_edit_toolbar(self.view, "user_form", with_split_save=False))
        if self.user.pk:
            self._build_existing_user()

    def _build_existing_user(self):
        user = self.user
        change_password_button = DropdownItem(
            url=reverse("shuup_admin:user.change-password", kwargs={"pk": user.pk}),
            text=_(u"Change Password"), icon="fa fa-exchange"
        )
        reset_password_button = DropdownItem(
            url=reverse("shuup_admin:user.reset-password", kwargs={"pk": user.pk}),
            disable_reason=(_("User has no email address") if not getattr(user, 'email', '') else None),
            text=_(u"Send Password Reset Email"), icon="fa fa-envelope"
        )
        permissions_button = DropdownItem(
            url=reverse("shuup_admin:user.change-permissions", kwargs={"pk": user.pk}),
            text=_(u"Edit Permissions"), icon="fa fa-lock", required_permissions=["auth.change_permission"]
        )
        menu_items = [
            change_password_button,
            reset_password_button,
            permissions_button,
            DropdownDivider()
        ]

        person_contact = PersonContact.objects.filter(user=user).first()
        if person_contact:
            contact_url = reverse("shuup_admin:contact.detail", kwargs={"pk": person_contact.pk})
            menu_items.append(DropdownItem(
                url=contact_url,
                icon="fa fa-search",
                text=_(u"Contact Details"),
            ))
        else:
            contact_url = reverse("shuup_admin:contact.new") + "?type=person&user_id=%s" % user.pk
            menu_items.append(DropdownItem(
                url=contact_url,
                icon="fa fa-plus",
                text=_(u"New Contact"),
                tooltip=_("Create a new contact and associate it with this user")
            ))
        self.append(DropdownActionButton(
            menu_items,
            icon="fa fa-star",
            text=_(u"Actions"),
            extra_css_class="btn-info",
        ))
        if not user.is_active:
            self.append(PostActionButton(
                post_url=self.request.path,
                name="set_is_active",
                value="1",
                icon="fa fa-check-circle",
                text=_(u"Activate User"),
                extra_css_class="btn-gray",
            ))
        else:
            self.append(PostActionButton(
                post_url=self.request.path,
                name="set_is_active",
                value="0",
                icon="fa fa-times-circle",
                text=_(u"Deactivate User"),
                extra_css_class="btn-gray",
            ))

        if (self.request.user.is_superuser and get_front_url() and
                user.is_active and not user.is_superuser and not user.is_staff):
            self.append(PostActionButton(
                post_url=reverse("shuup_admin:user.login-as", kwargs={"pk": user.pk}),
                text=_(u"Login as User"),
                extra_css_class="btn-gray"
            ))
        # TODO: Add extensibility


class UserDetailView(CreateOrUpdateView):
    # Model set during dispatch because it's swappable
    template_name = "shuup/admin/users/detail.jinja"
    context_object_name = "user"
    _fields = ["username", "email", "first_name", "last_name"]

    @property
    def fields(self):
        # check whether these fields exists in the model or it has the attribute
        model_fields = self.model._meta.get_all_field_names()
        return [field for field in self._fields if field in model_fields or hasattr(self.model, field)]

    def get_form_class(self):
        return modelform_factory(self.model, form=BaseUserForm, fields=self.fields)

    def _get_bind_contact(self):
        contact_id = self.request.REQUEST.get("contact_id")
        if contact_id:
            return Contact.objects.get(pk=contact_id)
        return None

    def get_initial(self):
        initial = super(UserDetailView, self).get_initial()
        contact = self._get_bind_contact()
        if contact:
            # Guess some sort of usable username
            username = flatten(contact, ".")
            if len(username) < 3:
                username = getattr(contact, "email", "").split("@")[0]
            if len(username) < 3:
                username = "user%08d" % random.randint(0, 99999999)
            initial.update(
                username=username,
                email=getattr(contact, "email", ""),
                first_name=getattr(contact, "first_name", ""),
                last_name=getattr(contact, "last_name", ""),
            )
        return initial

    def get_toolbar(self):
        return UserDetailToolbar(view=self)

    @atomic
    def save_form(self, form):
        self.object = form.save()
        contact = self._get_bind_contact()
        if contact and not contact.user:
            contact.user = self.object
            contact.save()
            messages.info(self.request, _(u"User bound to contact %(contact)s.") % {"contact": contact})

    def get_success_url(self):
        return get_model_url(self.object)

    def _handle_set_is_active(self):
        state = bool(int(self.request.POST["set_is_active"]))
        if not state:
            if (getattr(self.object, 'is_superuser', False) and not getattr(self.request.user, 'is_superuser', False)):
                raise Problem(_("You can not deactivate a superuser."))
            if self.object == self.request.user:
                raise Problem(_("You can not deactivate yourself."))

        self.object.is_active = state
        self.object.save(update_fields=("is_active",))
        messages.success(self.request, _("%(user)s is now %(state)s.") % {
            "user": self.object,
            "state": _("active") if state else _("inactive")
        })
        return HttpResponseRedirect(self.request.path)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "set_is_active" in request.POST:
            return self._handle_set_is_active()
        return super(UserDetailView, self).post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.model = get_user_model()
        return super(UserDetailView, self).dispatch(request, *args, **kwargs)


class LoginAsUserView(DetailView):
    model = get_user_model()

    def post(self, request, *args, **kwargs):
        front_url = get_front_url()
        user = self.get_object()
        username_field = self.model.USERNAME_FIELD
        impersonator_user_id = request.user.pk

        if not front_url:
            raise Problem(_("No shop configured."))
        if user == request.user:
            raise Problem(_("You are already logged in."))
        if not getattr(request.user, "is_superuser", False):
            raise PermissionDenied
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            raise PermissionDenied
        if not getattr(user, "is_active", False):
            raise Problem(_("This user is not active."))

        if not hasattr(user, 'backend'):
            for backend in django_settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
                    break

        login(request, user)
        request.session["impersonator_user_id"] = impersonator_user_id
        message = _("You're now logged in as {username}").format(username=user.__dict__[username_field])
        messages.success(request, message)
        return HttpResponseRedirect(front_url)
