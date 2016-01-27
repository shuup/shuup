# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import abc

import six
from django.conf import settings

from shoop.apps.provides import load_modules


def get_basket_campaign_modules():
    """
    Get a list of active basket discount module instances.

    :rtype: list[BasketCampaignModule]
    """

    return _get_campaign_modules("SHOOP_BASKET_CAMPAIGN_MODULES", "basket_campaign_module")


def get_catalog_campaign_modules():
    """
    Get a list of active catalog discount module instances.

    :rtype: list[CatalogCampaignModule]
    """

    return _get_campaign_modules("SHOOP_CATALOG_CAMPAIGN_MODULES", "catalog_campaign_module")


def _get_campaign_modules(setting_name, provide_category):
    modules = []
    if getattr(settings, setting_name, None):
        # `load_modules` would error out at the setting being falsy,
        # so handle that here instead.
        for cls in load_modules(setting_name, provide_category):
            modules.append(cls())
    return modules


class CatalogCampaignModule(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def discount_price(self, context, price_info, product):
        # TODO (campaigns) docstring
        pass


class BasketCampaignModule(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_basket_campaign_lines(self, order_source, lines):
        # TODO (campaigns) docstring
        pass
