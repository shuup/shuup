# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup import configuration

SAMPLE_BUSINESS_SEGMENT_KEY = "sample_business_segment"
SAMPLE_PRODUCTS_KEY = "sample_products"
SAMPLE_CATEGORIES_KEY = "sample_categories"
SAMPLE_CAROUSEL_KEY = "sample_carousel"


def get_installed_business_segment(shop):
    """ Returns the installed business segment """
    return configuration.get(shop, SAMPLE_BUSINESS_SEGMENT_KEY)


def get_installed_products(shop):
    """ Returns the installed products samples list """
    return configuration.get(shop, SAMPLE_PRODUCTS_KEY) or []


def get_installed_categories(shop):
    """ Returns the installed categories samples list """
    return configuration.get(shop, SAMPLE_CATEGORIES_KEY) or []


def get_installed_carousel(shop):
    """ Returns the installed sample carousel """
    return configuration.get(shop, SAMPLE_CAROUSEL_KEY)


def clear_installed_samples(shop):
    """ Clears all the samples values from the configuration """
    configuration.set(shop, SAMPLE_PRODUCTS_KEY, None)
    configuration.set(shop, SAMPLE_CATEGORIES_KEY, None)
    configuration.set(shop, SAMPLE_CAROUSEL_KEY, None)
    configuration.set(shop, SAMPLE_BUSINESS_SEGMENT_KEY, None)


def save_business_segment(shop, business_segment):
    """ Save the business segment identifier """
    configuration.set(shop, SAMPLE_BUSINESS_SEGMENT_KEY, business_segment)


def save_products(shop, products_pk):
    """ Save a list of PK as a list of sample products for a shop """
    configuration.set(shop, SAMPLE_PRODUCTS_KEY, products_pk)


def save_categories(shop, categories_pk):
    """ Save a list of PK as a list of sample categories for a shop """
    configuration.set(shop, SAMPLE_CATEGORIES_KEY, categories_pk)


def save_carousel(shop, carousel_pk):
    """ Save the PK of the sample carousel """
    configuration.set(shop, SAMPLE_CAROUSEL_KEY, carousel_pk)


def has_installed_samples(shop):
    """ Returns whether there is some sample data installed """
    return bool(
        get_installed_products(shop) or
        get_installed_categories(shop) or
        get_installed_carousel(shop)
    )
