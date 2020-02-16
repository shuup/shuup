# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import re
import unicodedata

from django.db import models
from django.utils.encoding import force_text


def get_model_unique_fields(model):
    for field in model._meta.local_fields:
        if isinstance(field, models.AutoField) or field.unique:
            yield field
    tmo = getattr(model._meta, "translations_model", None)
    if tmo:
        for field in get_model_unique_fields(tmo):
            if field.name not in ("master", "id", "language_code"):
                yield field


def get_model_possible_name_fields(model):
    for field in model._meta.local_fields:
        if field.name in ["name", "title"]:
            yield field
    if hasattr(model, "_parler_meta"):
        for field in model._parler_meta.root_model._meta.get_fields():
            if field.name not in ("master", "id", "language_code", "description"):
                yield field


def fold_mapping_name(m_name):
    m_name = force_text(m_name).strip().lower()
    m_name = force_text(unicodedata.normalize("NFKD", m_name).encode("ascii", "ignore"))
    m_name = re.sub(r"/[^a-z0-9]+/", "", m_name)
    return m_name.replace(" ", "_")


def get_global_aliases():
    """
    Get list of global aliases for fields
    :return:
    """
    return {
        "shop": ["store", "store_id", "_store"],
        "default_price_value": ["price", "original_price", "originalprice", "default_price"],
        "first_name": ["firstname"],
        "last_name": ["lastname"],
        "street": ["street_address", "address_street", "addr_street", "address[street]"],
        "country": ["country_id"],
        "slug": ["url_key", "url"],
        "phone": ["telephone"],
        "postal_code": [
            "postcode", "postalcode",
            "address_postcode", "address_postalcode", "address_postal_code",
            "address[postcode]", "address[postalcode]", "address[postal_code]"],
    }
