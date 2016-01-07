# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownItem,
    get_default_edit_toolbar, PostActionButton, Toolbar
)
from shoop.admin.utils.urls import get_model_url
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Contact, PersonContact
from shoop.utils.excs import Problem
from shoop.utils.text import flatten


class BaseUserForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    permission_info = forms.CharField(
        label=_("Permissions"),
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
                _("staff") if self.instance.is_staff else "",
                _("superuser") if self.instance.is_superuser else "",
            ] if perm) or _("No special permissions")
        else:
            self.fields.pop("permission_info")

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
            url=reverse("shoop_admin:user.change-password", kwargs={"pk": user.pk}),
            text=_(u"Change Password"), icon="fa fa-exchange"
        )
        reset_password_button = DropdownItem(
            url=reverse("shoop_admin:user.reset-password", kwargs={"pk": user.pk}),
            disable_reason=(_("User has no email address") if not user.email else None),
            text=_(u"Send Password Reset Email"), icon="fa fa-envelope"
        )
        permissions_button = DropdownItem(
            url=reverse("shoop_admin:user.change-permissions", kwargs={"pk": user.pk}),
            text=_(u"Edit Permissions"), icon="fa fa-lock"
        )
        menu_items = [
            change_password_button,
            reset_password_button,
            permissions_button,
            DropdownDivider()
        ]

        person_contact = PersonContact.objects.filter(user=user).first()
        if person_contact:
            contact_url = reverse("shoop_admin:contact.detail", kwargs={"pk": person_contact.pk})
            menu_items.append(DropdownItem(
                url=contact_url,
                icon="fa fa-search",
                text=_(u"Contact Details"),
            ))
        else:
            contact_url = reverse("shoop_admin:contact.new") + "?user_id=%s" % user.pk
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
        # TODO: Add extensibility


class UserDetailView(CreateOrUpdateView):
    # Model set during dispatch because it's swappable
    template_name = "shoop/admin/users/detail.jinja"
    context_object_name = "user"
    fields = ("username", "email", "first_name", "last_name")

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
            if (self.object.is_superuser and not self.request.user.is_superuser):
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
