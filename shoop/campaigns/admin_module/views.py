# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from babel.dates import format_datetime
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.toolbar import NewActionButton, Toolbar
from shoop.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shoop.admin.utils.views import CreateOrUpdateView, PicotableListView
from shoop.campaigns.forms import (
    BasketCampaignForm, CatalogCampaignForm, CouponForm
)
from shoop.campaigns.models.campaigns import (
    BasketCampaign, CatalogCampaign, Coupon
)
from shoop.utils.i18n import format_percent, get_current_babel_locale


class _Breadcrumbed(object):
    def get_breadcrumb_parents(self):
        return [MenuEntry(text=self.parent_name, url=self.parent_url)]


class CampaignListView(PicotableListView):
    columns = [
        Column(
            "name", _(u"Title"), sort_field="name", display="name", linked=True,
            filter_config=TextFilter(operator="startswith")
        ),
        Column("discount_percentage", _("Discount percentage"), display="format_percentage"),
        Column("discount_amount", _("Discount amount"), sort_field="discount_amount_value"),
        Column("start_datetime", _("Starts")),
        Column("end_datetime", _("Ends")),
        Column("active", _("Active"), filter_config=ChoicesFilter(choices=[(0, _("No")), (1, _("Yes"))])),
    ]

    def format_percentage(self, instance, *args, **kwargs):
        if not instance.discount_percentage:
            return ""
        return format_percent(instance.discount_percentage)

    def start_datetime(self, instance, *args, **kwargs):
        if not instance.start_datetime:
            return ""
        return self._formatted_datetime(instance.start_datetime)

    def end_datetime(self, instance, *args, **kwargs):
        if not instance.end_datetime:
            return ""
        return self._formatted_datetime(instance.end_datetime)

    def _formatted_datetime(self, dt):
        return format_datetime(localtime(dt), locale=get_current_babel_locale())

    def add_columns(self, column_id, columns, after=True):
        # TODO: Make better
        added = False
        for idx, column in enumerate(self.columns):
            if column.id == column_id:
                found_idx = idx + 1 if after else idx
                start = self.columns[:found_idx]
                end = self.columns[found_idx:]
                self.columns = start + columns + end
                added = True
                break

        if not added:
            self.columns += columns

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % (instance or _("CatalogCampaign")), "class": "header"},
        ]


class CatalogCampaignListView(CampaignListView):
    model = CatalogCampaign

    def __init__(self, **kwargs):
        new_columns = [
            Column("conditions", _("Used Conditions")),
            Column("filters", _("Used filters")),
        ]
        self.add_columns("name", new_columns)
        super(CatalogCampaignListView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(CampaignListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            NewActionButton("shoop_admin:catalog_campaigns.new", text=_("Create new Catalog Campaign")),
        ])
        return context


class BasketCampaignListView(CampaignListView):
    model = BasketCampaign

    def __init__(self, **kwargs):
        new_columns = [
            Column("conditions", _("Used Conditions")),
            Column("coupon", _("Discount Code")),
        ]
        self.add_columns("name", new_columns)
        super(BasketCampaignListView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(CampaignListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            NewActionButton("shoop_admin:basket_campaigns.new", text=_("Create new Basket Campaign")),
        ])
        return context


class CampaignEditView(CreateOrUpdateView):
    template_name = "shoop/campaigns/admin/edit_campaigns.jinja"

    context_object_name = "campaign"
    add_form_errors_as_messages = True

    def get_form_kwargs(self):
        kwargs = super(CampaignEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class CatalogCampaignEditView(_Breadcrumbed, CampaignEditView):
    model = CatalogCampaign
    form_class = CatalogCampaignForm
    parent_name = _("Catalog Campaign")
    parent_url = "shoop_admin:catalog_campaigns.list"


class BasketCampaignEditView(_Breadcrumbed, CampaignEditView):
    model = BasketCampaign
    form_class = BasketCampaignForm
    parent_name = _("Basket Campaign")
    parent_url = "shoop_admin:basket_campaigns.list"


class CouponListView(PicotableListView):
    model = Coupon
    columns = [
        Column(
            "code", _(u"Code"), sort_field="code", display="code", linked=True,
            filter_config=TextFilter(operator="startswith")
        ),
        Column("usages", _("Usages"), display="get_usages"),
        Column("usage_limit_customer", _("Usages Limit per contact")),
        Column("usage_limit", _("Usage Limit")),
        Column("active", _("Active")),
        Column("created_by", _(u"Created by")),
        Column("created_on", _(u"Date created")),
    ]

    def get_usages(self, instance, *args, **kwargs):
        return instance.usages.count()

    def get_context_data(self, **kwargs):
        context = super(CouponListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            NewActionButton("shoop_admin:coupons.new", text=_("Create new Coupon")),
        ])
        return context


class CouponEditView(_Breadcrumbed, CreateOrUpdateView):
    model = Coupon
    template_name = "shoop/campaigns/admin/edit_coupons.jinja"
    form_class = CouponForm
    context_object_name = "coupon"
    add_form_errors_as_messages = True
    parent_name = _("Coupon")
    parent_url = "shoop_admin:coupons.list"
