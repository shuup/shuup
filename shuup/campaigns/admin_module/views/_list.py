# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from babel.dates import format_datetime
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.campaigns.models.campaigns import (
    BasketCampaign, CatalogCampaign, Coupon
)
from shuup.utils.i18n import get_current_babel_locale


class CampaignListView(PicotableListView):
    default_columns = [
        Column(
            "name", _(u"Title"), sort_field="name", display="name", linked=True,
            filter_config=TextFilter(operator="startswith")
        ),
        Column("start_datetime", _("Starts")),
        Column("end_datetime", _("Ends")),
        Column("active", _("Active"), filter_config=ChoicesFilter(choices=[(0, _("No")), (1, _("Yes"))])),
    ]

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

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % (instance or _("CatalogCampaign")), "class": "header"},
        ]


class CatalogCampaignListView(CampaignListView):
    model = CatalogCampaign

    def get_context_data(self, **kwargs):
        context = super(CampaignListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            NewActionButton("shuup_admin:catalog_campaign.new", text=_("Create new Catalog Campaign")),
            SettingsActionButton.for_model(self.model, return_url="catalog-campaign")
        ])
        return context


class BasketCampaignListView(CampaignListView):
    model = BasketCampaign

    def get_context_data(self, **kwargs):
        context = super(CampaignListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([
            NewActionButton("shuup_admin:basket_campaign.new", text=_("Create new Basket Campaign")),
            SettingsActionButton.for_model(self.model, return_url="basket-campaign")
        ])
        return context


class CouponListView(PicotableListView):
    model = Coupon
    default_columns = [
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
            NewActionButton("shuup_admin:coupon.new", text=_("Create new Coupon")),
            SettingsActionButton.for_model(self.model, return_url="coupon")
        ])
        print(context["toolbar"])
        return context
