# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.core.models._addresses import Address
from shuup.utils.django_compat import force_text
from shuup.utils.i18n import get_current_babel_locale


class BaseAddressFormatter(object):
    def address_as_string_list(self, address, locale=None):
        raise NotImplementedError()


class DefaultAddressFormatter(BaseAddressFormatter):
    def address_as_string_list(self, address, locale=None):
        assert issubclass(type(address), Address)

        locale = locale or get_current_babel_locale()
        country = address.country.code.upper()

        base_lines = [
            address.company_name,
            address.full_name,
            address.name_ext,
            address.street,
            address.street2,
            address.street3,
            "%s %s %s" % (address.postal_code, address.city, address.region_code or address.region),
            locale.territories.get(country, country) if not address.is_home else None,
        ]

        stripped_lines = [force_text(line).strip() for line in base_lines if line]
        return [s for s in stripped_lines if (s and len(s) > 1)]
