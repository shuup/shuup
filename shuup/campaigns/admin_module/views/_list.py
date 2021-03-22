# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from babel.dates import format_datetime
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.campaigns.models.campaigns import BasketCampaign, CatalogCampaign, Coupon
from shuup.utils.i18n import get_current_babel_locale


class CampaignListView(PicotableListView):
    default_columns = [
        Column(
            "name",
            _(u"Title"),
            sort_field="name",
            display="name",
            linked=True,
            filter_config=TextFilter(operator="startswith"),
        ),
        Column("start_datetime", _("Starts")),
        Column("end_datetime", _("Ends")),
        Column("active", _("Active"), filter_config=ChoicesFilter(choices=[(0, _("No")), (1, _("Yes"))])),
    ]
    toolbar_buttons_provider_key = "campaign_list_toolbar_provider"
    mass_actions_provider_key = "campaign_list_actions_provider"

    def get_queryset(self):
        return self.model.objects.filter(shop=get_shop(self.request))

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
        if self.request.user.is_superuser:
            settings_button = SettingsActionButton.for_model(self.model, return_url="catalog_campaign")
        else:
            settings_button = None
        context["toolbar"] = Toolbar(
            [
                NewActionButton("shuup_admin:catalog_campaign.new", text=_("Create new Catalog Campaign")),
                settings_button,
            ],
            view=self,
        )
        return context


class BasketCampaignListView(CampaignListView):
    model = BasketCampaign

    def get_context_data(self, **kwargs):
        context = super(CampaignListView, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            settings_button = SettingsActionButton.for_model(self.model, return_url="basket_campaign")
        else:
            settings_button = None
        context["toolbar"] = Toolbar(
            [NewActionButton("shuup_admin:basket_campaign.new", text=_("Create new Basket Campaign")), settings_button],
            view=self,
        )
        return context

    def get_queryset(self):
        queryset = super(BasketCampaignListView, self).get_queryset()
        supplier = get_supplier(self.request)
        if supplier:
            queryset = queryset.filter(supplier=supplier)
        return queryset


class CouponListView(PicotableListView):
    model = Coupon
    default_columns = [
        Column(
            "code",
            _(u"Code"),
            sort_field="code",
            display="code",
            linked=True,
            filter_config=TextFilter(operator="startswith"),
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
        if self.request.user.is_superuser:
            settings_button = SettingsActionButton.for_model(self.model, return_url="coupon")
        else:
            settings_button = None
        context["toolbar"] = Toolbar(
            [NewActionButton("shuup_admin:coupon.new", text=_("Create new Coupon")), settings_button], view=self
        )
        return context

    def get_queryset(self):
        queryset = super(CouponListView, self).get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(shop=get_shop(self.request))

        supplier = get_supplier(self.request)
        if supplier:
            queryset = queryset.filter(supplier=supplier)
        return queryset
