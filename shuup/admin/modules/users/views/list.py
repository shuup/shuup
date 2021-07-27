# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import ChoicesFilter, Column, Select2Filter, TextFilter, true_or_false_filter
from shuup.admin.utils.views import PicotableListView
from shuup.utils.django_compat import force_text


class UserListView(PicotableListView):
    model = settings.AUTH_USER_MODEL
    default_columns = [
        Column("username", _("Username"), filter_config=TextFilter()),
        Column("email", _("Email"), filter_config=TextFilter()),
        Column("first_name", _("First Name"), filter_config=TextFilter()),
        Column("last_name", _("Last Name"), filter_config=TextFilter()),
        Column(
            "is_active",
            _("Active"),
            filter_config=ChoicesFilter([(False, _("no")), (True, _("yes"))], default=True),
        ),
        Column("groups", _("Groups"), filter_config=Select2Filter("get_groups"), display="get_groups_display"),
        Column("is_staff", _("Access to Admin Panel"), filter_config=true_or_false_filter),
    ]
    toolbar_buttons_provider_key = "user_list_toolbar_provider"
    mass_actions_provider_key = "user_list_mass_actions_provider"

    def get_groups(self):
        return list(Group.objects.all().values_list("id", "name"))

    def get_groups_display(self, instance):
        groups = [group.name for group in instance.groups.all()]
        return ", ".join(groups) if groups else _("No group")

    def get_model(self):
        return get_user_model()

    def get_queryset(self):
        model = self.get_model()

        qs = self.get_model().objects.all().prefetch_related("groups")
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
        return [
            {"text": instance.get_username() or _("User"), "class": "header"},
            {"title": _("Email"), "text": item.get("email")},
            {"title": _("First Name"), "text": item.get("first_name")},
            {"title": _("Last Name"), "text": item.get("last_name")},
            {"title": _("Active"), "text": item.get("is_active")},
            {"title": _("Groups"), "text": item.get("groups")},
            {"title": _("Access to Admin Panel"), "text": item.get("is_staff")},
        ]
