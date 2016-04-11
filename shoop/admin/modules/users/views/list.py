# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from shoop.admin.utils.picotable import (
    Column, TextFilter, true_or_false_filter
)
from shoop.admin.utils.views import PicotableListView


class UserListView(PicotableListView):
    model = settings.AUTH_USER_MODEL
    columns = [
        Column("username", _(u"Username"), filter_config=TextFilter()),
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("first_name", _(u"First Name"), filter_config=TextFilter()),
        Column("last_name", _(u"Last Name"), filter_config=TextFilter()),
        Column("is_active", _(u"Active"), filter_config=true_or_false_filter),
        Column("is_staff", _(u"Staff"), filter_config=true_or_false_filter),
        Column("is_superuser", _(u"Superuser"), filter_config=true_or_false_filter),
    ]

    def get_model(self):
        return get_user_model()

    def get_queryset(self):
        return self.get_model().objects.all()

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
            _("Staff") if getattr(instance, 'is_staff', None) else None,
            _("Superuser") if getattr(instance, 'is_superuser', None) else None
        ])
        return [
            {"text": instance.get_username() or _("User"), "class": "header"},
            {"text": ", ".join(bits)}
        ]
