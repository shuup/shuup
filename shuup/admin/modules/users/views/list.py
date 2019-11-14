# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, TextFilter, true_or_false_filter
)
from shuup.admin.utils.views import PicotableListView
from shuup.utils.django_compat import force_text


class UserListView(PicotableListView):
    model = settings.AUTH_USER_MODEL
    default_columns = [
        Column("username", _(u"Username"), filter_config=TextFilter()),
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("first_name", _(u"First Name"), filter_config=TextFilter()),
        Column("last_name", _(u"Last Name"), filter_config=TextFilter()),
        Column(
            "is_active",
            _(u"Active"),
            filter_config=ChoicesFilter([(False, _("no")), (True, _("yes"))], default=True),
        ),
        Column("is_staff", _(u"Access to Admin Panel"), filter_config=true_or_false_filter),
        Column("is_superuser", _(u"Superuser (Full rights)"), filter_config=true_or_false_filter),
    ]
    toolbar_buttons_provider_key = "user_list_toolbar_provider"
    mass_actions_provider_key = "user_list_mass_actions_provider"

    def get_model(self):
        return get_user_model()

    def get_queryset(self):
        model = self.get_model()
        qs = self.get_model().objects.all()
        if "date_joined" in [f.name for f in model._meta.get_fields()]:
            qs = qs.order_by("-date_joined")

        # non superusers can't see superusers
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context["title"] = force_text(self.get_model()._meta.verbose_name_plural).title()
        return context

    def get_object_abstract(self, instance, item):
        bits = filter(None, [
            _("First Name: %s") % (getattr(instance, 'first_name', None) or "\u2014"),
            _("Last Name: %s") % (getattr(instance, 'last_name', None) or "\u2014"),
            _("Active") if instance.is_active else _(u"Inactive"),
            _("Email: %s") % (getattr(instance, 'email', None) or "\u2014"),
            _("Access to Admin Panel") if getattr(instance, 'is_staff', None) else None,
            _("Superuser (Full rights)") if getattr(instance, 'is_superuser', None) else None
        ])
        return [
            {"text": instance.get_username() or _("User"), "class": "header"},
            {"text": ", ".join([force_text(bit) for bit in bits])}
        ]
