# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random

from django import forms
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model, load_backend, login
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.transaction import atomic
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import (
    DropdownActionButton, DropdownDivider, DropdownItem,
    get_default_edit_toolbar, PostActionButton, Toolbar
)
from shuup.admin.utils.permissions import has_permission
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Contact, PersonContact
from shuup.front.apps.registration.signals import user_reactivated
from shuup.utils.django_compat import force_text, NoReverseMatch, reverse
from shuup.utils.excs import Problem
from shuup.utils.text import flatten

NEW_USER_EMAIL_CONFIRMATION_TEMPLATE = _("""
    Welcome %(first_name)s!

    You've been added as an administrator to %(shop_url)s. Here are some details:
        Shop url: %(shop_url)s
        Login url: %(admin_url)s
        Your username: '%(username)s'
        Your password: Please contact your admin.
""")


def get_front_url():
    front_url = None
    try:
        front_url = reverse(django_settings.SHUUP_ADMIN_LOGIN_AS_REDIRECT_VIEW)
    except NoReverseMatch:
        front_url = None
    return front_url


def get_admin_url():
    admin_url = None
    try:
        admin_url = reverse(django_settings.SHUUP_ADMIN_LOGIN_AS_STAFF_REDIRECT_VIEW)
    except NoReverseMatch:
        admin_url = None
    return admin_url


class BaseUserForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, help_text=_(
        "The user password."
    ))
    permission_info = forms.CharField(
        label=_("Main Permissions"),
        widget=forms.TextInput(attrs={"readonly": True, "disabled": True}),
        required=False,
        help_text=_("Two fundamental permissions: Access to Admin Panel and "
                    "Superuser status rights. Go to user account -> `Actions` "
                    "-> `Edit Main Permissions` to change these.")
    )
    permission_groups = forms.CharField(
        label=_("Granular Permission Groups"),
        widget=forms.TextInput(attrs={"readonly": True, "disabled": True}),
        required=False,
        help_text=_(
            "Use Permission Groups to granularly give more permissions. "
            "Search for `Permission Groups` to change these and add them to "
            "multiple users. Go to user account -> `Actions` -> `Edit Main "
            "Permissions` to add them to a specific user. Will not influence "
            "Superusers as they already have all the rights and can't be "
            "stripped of them without removing Superuser status first."
        )
    )

    def __init__(self, *args, **kwargs):
        super(BaseUserForm, self).__init__(*args, **kwargs)
        if "email" in self.fields:
            self.fields["email"].help_text = _("The user email address. Used for password resets.")
        if "first_name" in self.fields:
            self.fields["first_name"].help_text = _("The first name of the user.")
        if "last_name" in self.fields:
            self.fields["last_name"].help_text = _("The last name of the user.")
        if self.instance.pk:
            # Changing the password for an existing user requires more confirmation
            self.fields.pop("password")
            self.initial["permission_info"] = ", ".join(force_text(perm) for perm in [
                _("Access to Admin Panel") if getattr(self.instance, 'is_staff', None) else "",
                _("Superuser (Full rights)") if getattr(self.instance, 'is_superuser', None) else "",
            ] if perm) or _("No Main Permissions selected.")
            if hasattr(self.instance, "groups"):
                group_names = [force_text(group) for group in self.instance.groups.all()]
                if group_names:
                    self.initial["permission_groups"] = ", ".join(sorted(group_names))
                else:
                    self.initial["permission_groups"] = _("No Granular Permission Groups selected.")
            else:
                self.initial["permission_groups"] = _("No Granular Permission Groups available.")
        else:
            self.fields.pop("permission_info")
            self.fields.pop("permission_groups")
            if "email" in self.fields:
                self.fields["send_confirmation"] = forms.BooleanField(
                    label=_("Send email confirmation"),
                    initial=True,
                    required=False,
                    help_text=_(
                        "Send an email to the user to let them know they've "
                        "been added as a shop user. Applicable only for users "
                        "with Access to Admin Panel status."
                    )
                )

    def clean(self):
        cleaned_data = super(BaseUserForm, self).clean()
        if (
            cleaned_data.get("send_confirmation") and
            cleaned_data.get("is_staff") and
            not self.cleaned_data.get("email")
        ):
            raise forms.ValidationError({"email": _("Please enter an email to send a confirmation to.")})

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
            text=_(u"Change Password"), icon="fa fa-exchange",
            required_permissions=["user.change-password"]
        )
        reset_password_button = DropdownItem(
            url=reverse("shuup_admin:user.reset-password", kwargs={"pk": user.pk}),
            disable_reason=(_("User has no email address") if not getattr(user, 'email', '') else None),
            text=_(u"Send Password Reset Email"), icon="fa fa-envelope",
            required_permissions=["user.reset-password"]
        )
        permissions_button = DropdownItem(
            url=reverse("shuup_admin:user.change-permissions", kwargs={"pk": user.pk}),
            text=_(u"Edit Main Permissions"), icon="fa fa-lock", required_permissions=["user.change-permissions"]
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
                text=_("Contact Details"),
                required_permissions=["contact.detail"]
            ))
        else:
            contact_url = reverse("shuup_admin:contact.new") + "?type=person&user_id=%s" % user.pk
            menu_items.append(DropdownItem(
                url=contact_url,
                icon="fa fa-plus",
                text=_(u"New Contact"),
                tooltip=_("Create a new contact and associate it with this user"),
                required_permissions=["contact.new"]
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

        current_user = self.request.user
        is_current_user_superuser_or_staff = (
            getattr(current_user, "is_superuser", False) or
            getattr(current_user, "is_staff", False)
        )
        can_impersonate = bool(
            is_current_user_superuser_or_staff and user.is_active and not user.is_superuser
        )

        if (can_impersonate and get_front_url() and not user.is_staff):
            self.append(PostActionButton(
                post_url=reverse("shuup_admin:user.login-as", kwargs={"pk": user.pk}),
                text=_(u"Login as User"),
                extra_css_class="btn-gray"
            ))
        elif (can_impersonate and get_admin_url() and user.is_staff):
            self.append(PostActionButton(
                post_url=reverse("shuup_admin:user.login-as-staff", kwargs={"pk": user.pk}),
                text=_(u"Login as Staff User"),
                extra_css_class="btn-gray"
            ))
        # TODO: Add extensibility


class UserDetailView(CreateOrUpdateView):
    # Model set during dispatch because it's swappable
    template_name = "shuup/admin/users/detail.jinja"
    context_object_name = "user"
    _fields = ["username", "email", "first_name", "last_name", "password"]

    @property
    def fields(self):
        # check whether these fields exists in the model or it has the attribute
        model_fields = [f.name for f in self.model._meta.get_fields()]
        fields = [field for field in self._fields if field in model_fields or hasattr(self.model, field)]
        if not self.object.pk and getattr(self.request.user, "is_superuser", False):
            fields.append("is_staff")
            fields.append("is_superuser")
        return fields

    def get_form_class(self):
        return modelform_factory(self.model, form=BaseUserForm, fields=self.fields)

    def _get_bind_contact(self):
        contact_id = self.request.GET.get("contact_id")
        if contact_id:
            return Contact.objects.get(pk=contact_id)
        return None

    def get_queryset(self):
        qs = super(UserDetailView, self).get_queryset()

        # non superusers can't see superusers
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)

        return qs

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
            messages.info(self.request, _(u"Info! User bound to contact %(contact)s.") % {"contact": contact})

        if getattr(self.object, "is_staff", False) and form.cleaned_data.get("send_confirmation"):
            shop_url = "%s://%s/" % (self.request.scheme, self.request.get_host())
            admin_url = self.request.build_absolute_uri(reverse("shuup_admin:login"))
            send_mail(
                subject=_("You've been added as an admin user to `%s`." % shop_url),
                message=NEW_USER_EMAIL_CONFIRMATION_TEMPLATE % {
                    "first_name": getattr(self.object, "first_name") or getattr(self.object, "username", _("User")),
                    "shop_url": shop_url,
                    "admin_url": admin_url,
                    "username": getattr(self.object, "username") or getattr(self.object.email)
                },
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.object.email]
            )

    def _handle_set_is_active(self):
        state = bool(int(self.request.POST["set_is_active"]))
        if not state:
            if (getattr(self.object, 'is_superuser', False) and not getattr(self.request.user, 'is_superuser', False)):
                raise Problem(_("You can not deactivate a Superuser. Remove Superuser status first."))
            if self.object == self.request.user:
                raise Problem(_("You can not deactivate yourself. Use another account."))

        if not self.object.is_active and state:
            user_reactivated.send(sender=self.__class__, user=self.object, request=self.request)

        self.object.is_active = state
        self.object.save(update_fields=("is_active",))

        if hasattr(self.object, "contact"):
            self.object.contact.is_active = state
            self.object.contact.save(update_fields=("is_active",))

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


def _check_for_login_as_problems(redirect_url, impersonator_user, user):
    if not redirect_url:
        raise Problem(_("No shop configured."))
    if user == impersonator_user:
        raise Problem(_("You are already logged in."))
    if not getattr(user, "is_active", False):
        raise Problem(_("This user is not active."))


def _check_for_login_as_permissions(shop, impersonator_user, user, permission_str, can_impersonate_staff=False):
    if getattr(user, "is_superuser", False):
        raise PermissionDenied
    if getattr(user, "is_staff", False) and not can_impersonate_staff:
        raise PermissionDenied
    if not (getattr(impersonator_user, "is_superuser", False) or getattr(impersonator_user, "is_staff", False)):
        raise PermissionDenied
    if not (
        getattr(impersonator_user, "is_superuser", False) or
        shop.staff_members.filter(id=impersonator_user.pk).exists()
    ):
        raise PermissionDenied
    if not has_permission(impersonator_user, permission_str):
        raise PermissionDenied


class LoginAsUserView(DetailView):
    model = get_user_model()
    can_impersonate_staff = False
    permission_str = "user.login-as"

    def get_url(self):
        return get_front_url()

    def post(self, request, *args, **kwargs):
        redirect_url = self.get_url()
        user = self.get_object()
        username_field = self.model.USERNAME_FIELD
        impersonator_user = request.user
        impersonator_user_id = request.user.pk
        shop = get_shop(request)

        _check_for_login_as_problems(redirect_url, impersonator_user, user)
        _check_for_login_as_permissions(
            shop, impersonator_user, user, self.permission_str, self.can_impersonate_staff)

        if not hasattr(user, 'backend'):
            for backend in django_settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
                    break

        login(request, user)
        request.session["impersonator_user_id"] = impersonator_user_id
        message = _("You're now logged in as `{username}`.").format(username=user.__dict__[username_field])
        messages.success(request, message)
        return HttpResponseRedirect(redirect_url)


class LoginAsStaffUserView(LoginAsUserView):
    model = get_user_model()
    can_impersonate_staff = True
    permission_str = "user.login-as-staff"

    def get_url(self):
        return get_admin_url()
