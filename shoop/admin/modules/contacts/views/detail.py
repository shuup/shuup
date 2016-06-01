# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shoop.admin.toolbar import PostActionButton, Toolbar, URLActionButton
from shoop.core.models import CompanyContact, Contact, Order, PersonContact
from shoop.utils.excs import Problem


class ContactDetailToolbar(Toolbar):
    def __init__(self, contact, request):
        self.contact = contact
        self.request = request
        self.user = getattr(self.contact, "user", None)
        super(ContactDetailToolbar, self).__init__()
        self.build()

    def build_renew_password_button(self):
        disable_reason = None

        if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
            disable_reason = _("The Shoop frontend is not enabled.")
        elif not self.user:
            disable_reason = _("Contact has no associated user.")
        elif not getattr(self.user, "email", None):
            disable_reason = _("User has no associated email.")

        self.append(PostActionButton(
            post_url=reverse("shoop_admin:contact.reset_password", kwargs={"pk": self.contact.pk}),
            name="pk",
            value=self.contact.pk,
            text=_(u"Reset password"),
            tooltip=_(u"Send a password renewal email."),
            confirm=_("Are you sure you wish to send a password recovery email to %s?") % self.contact.email,
            icon="fa fa-undo",
            disable_reason=disable_reason,
            extra_css_class="btn-gray btn-inverse",
        ))

    def build_new_user_button(self):
        if self.user or isinstance(self.contact, CompanyContact):
            return
        self.append(URLActionButton(
            url=reverse("shoop_admin:user.new") + "?contact_id=%s" % self.contact.pk,
            text=_(u"New User"),
            tooltip=_(u"Create an user for the contact."),
            icon="fa fa-star",
            extra_css_class="btn-gray btn-inverse",
        ))

    def build_deactivate_button(self):
        self.append(PostActionButton(
            post_url=self.request.path,
            name="set_is_active",
            value="0" if self.contact.is_active else "1",
            icon="fa fa-times-circle",
            text=_(u"Deactivate Contact") if self.contact.is_active else _(u"Activate Contact"),
            extra_css_class="btn-gray",
        ))

    def build(self):
        self.append(URLActionButton(
            url=reverse("shoop_admin:contact.edit", kwargs={"pk": self.contact.pk}),
            icon="fa fa-pencil",
            text=_(u"Edit..."),
            extra_css_class="btn-info",
        ))
        self.build_renew_password_button()
        self.build_new_user_button()
        self.build_deactivate_button()


class ContactDetailView(DetailView):
    model = Contact
    template_name = "shoop/admin/contacts/detail.jinja"
    context_object_name = "contact"

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context["companies"] = []
        if isinstance(self.object, PersonContact):
            order_q = Q(orderer=self.object) | Q(customer=self.object)
            context["companies"] = sorted(
                self.object.company_memberships.all(), key=(lambda x: force_text(x))
            )
        else:
            order_q = Q(customer=self.object)
        user = getattr(self.object, "user", None)
        if user:
            order_q |= Q(creator=user)
        context["contact_groups"] = sorted(
            self.object.groups.all(), key=(lambda x: force_text(x)))
        context["orders"] = Order.objects.filter(order_q).order_by("-id")
        context["toolbar"] = ContactDetailToolbar(contact=self.object, request=self.request)
        context["title"] = "%s: %s" % (
            self.object._meta.verbose_name.title(),
            force_text(self.object)
        )
        return context

    def _handle_set_is_active(self):
        state = bool(int(self.request.POST["set_is_active"]))
        if not state and hasattr(self.object, "user"):
            if (getattr(self.object.user, 'is_superuser', False) and
                    not getattr(self.request.user, 'is_superuser', False)):
                raise Problem(_("You can not deactivate a superuser."))
            if self.object.user == self.request.user:
                raise Problem(_("You can not deactivate yourself."))

        self.object.is_active = state
        self.object.save(update_fields=("is_active",))
        messages.success(self.request, _("%(contact)s is now %(state)s.") % {
            "contact": self.object,
            "state": _("active") if state else _("inactive")
        })
        return HttpResponseRedirect(self.request.path)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "set_is_active" in request.POST:
            return self._handle_set_is_active()
        return super(ContactDetailView, self).post(request, *args, **kwargs)
