# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _

PRODUCT_SORT_CHOICES = [
    ("name_a", _(u"Name - A-Z")),
    ("name_d", _(u"Name - Z-A")),
    ("price_a", _(u"Price - Low to High")),
    ("price_d", _(u"Price - High to Low")),
]


def sort_products(request, products, sort):
    if not sort:
        sort = ""
    # Force sorting despite what collation says
    sorter = _get_product_name_lowered_stripped

    key = (sort[:-2] if sort.endswith(('_a', '_d')) else sort)
    reverse = bool(sort.endswith('_d'))

    if key == "name":
        sorter = _get_product_name_lowered
    elif key == "price":
        sorter = _get_product_price_getter_for_request(request)

    if sorter:
        products = sorted(products, key=sorter, reverse=reverse)

    return products


def _get_product_name_lowered_stripped(product):
    return product.name.lower().strip()


def _get_product_name_lowered(product):
    return product.name.lower()


def _get_product_price_getter_for_request(request):
    def _get_product_price(product):
        return product.get_price(request)
    return _get_product_price
