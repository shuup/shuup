# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.contacts.utils import request_limited
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, RangeFilter, Select2Filter, TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import (
    CompanyContact, Contact, ContactGroup, PersonContact, Shop
)


class ContactTypeFilter(ChoicesFilter):
    def __init__(self):
        super(ContactTypeFilter, self).__init__(choices=[("person", _("Person")), ("company", _("Company"))])

    def filter_queryset(self, queryset, column, value, context):
        if value == "_all":
            return queryset
        model_class = PersonContact
        if value == "company":
            model_class = CompanyContact
        return queryset.instance_of(model_class)


class ContactListView(PicotableListView):
    model = Contact
    default_columns = [
        Column("name", _(u"Name"), linked=True, filter_config=TextFilter()),
        Column("type", _(u"Type"), display="get_type_display", sortable=False, filter_config=ContactTypeFilter()),
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("phone", _(u"Phone"), filter_config=TextFilter()),
        Column(
            "is_active",
            _(u"Active"),
            filter_config=ChoicesFilter([(False, _("no")), (True, _("yes"))], default=True)
        ),
        Column("n_orders", _(u"# Orders"), class_name="text-right", filter_config=RangeFilter(step=1)),
        Column("groups", _("Groups"),
               filter_config=ChoicesFilter(ContactGroup.objects.all_except_defaults(), "groups"),
               display="get_groups_display"),
        Column("shops", _("Shops"), filter_config=Select2Filter("get_shops"), display="get_shops_display"),
        Column("registration_shop", _("Registered in"), filter_config=Select2Filter("get_shops"))
    ]

    mass_actions = [
        "shuup.admin.modules.contacts.mass_actions:EditContactsAction",
        "shuup.admin.modules.contacts.mass_actions:EditContactGroupsAction",
    ]
    toolbar_buttons_provider_key = "contact_list_toolbar_provider"
    mass_actions_provider_key = "contact_list_mass_actions_provider"

    def get_shops(self):
        return Shop.objects.get_for_user(self.request.user)

    def get_toolbar(self):
        if self.request.user.is_superuser:
            settings_button = SettingsActionButton.for_model(Contact, return_url="contact")
        else:
            settings_button = None
        return Toolbar([
            NewActionButton.for_model(
                PersonContact, url=reverse("shuup_admin:contact.new") + "?type=person"
            ),
            NewActionButton.for_model(
                CompanyContact, extra_css_class="btn-info", url=reverse("shuup_admin:contact.new") + "?type=company"
            ),
            settings_button
        ], view=self)

    def get_queryset(self):
        qs = super(ContactListView, self).get_queryset()
        groups = self.get_filter().get("groups")
        query = Q(groups__in=groups) if groups else Q()

        # non superusers can't see superusers contacts
        if not self.request.user.is_superuser:
            qs = qs.exclude(PersonContact___user__is_superuser=True)

        if self.request.GET.get("shop"):
            qs = qs.filter(shops=Shop.objects.get_for_user(self.request.user).filter(pk=self.request.GET["shop"]))

        elif request_limited(self.request):
            shop = get_shop(self.request)
            qs = qs.filter(shops=shop)

        return (
            qs
            .filter(query)
            .annotate(n_orders=Count("customer_orders"))
            .order_by("-created_on")
        )

    def get_type_display(self, instance):
        if isinstance(instance, PersonContact):
            return _(u"Person")
        elif isinstance(instance, CompanyContact):
            return _(u"Company")
        else:
            return _(u"Contact")

    def get_groups_display(self, instance):
        groups = instance.groups.all_except_defaults().values_list("translations__name", flat=True)
        return ", ".join(groups) if groups else _("No group")

    def get_shops_display(self, instance):
        user = self.request.user
        shops = instance.shops.get_for_user(user=user).values_list("translations__name", flat=True)
        return ", ".join(shops) if shops else _("No shops")

    def get_object_abstract(self, instance, item):
        """
        :type instance: shuup.core.models.Contact
        """
        bits = filter(None, [
            self.get_type_display(instance),
            _("Active") if instance.is_active else _("Inactive"),
            _("Email: %s") % (instance.email or "\u2014"),
            _("Phone: %s") % (instance.phone or "\u2014"),
            _("%d orders") % instance.n_orders,
        ])
        return [
            {"text": instance.name or _("Contact"), "class": "header"},
            {"text": ", ".join([force_text(bit) for bit in bits])}
        ]
