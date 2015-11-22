# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.test import override_settings

from shoop.front.checkout.addresses import AddressForm
from shoop.front.checkout.single_page import AddressForm as SinglePageAddressForm


def test_checkout_addresses_has_no_default_country():
    form = AddressForm()
    assert form.fields["country"].initial is None


@override_settings(SHOOP_ADDRESS_HOME_COUNTRY="FI")
def test_checkout_addresses_has_default_country():
    form = AddressForm()
    assert form.fields["country"].initial == "FI"


def test_checkout_singlepage_addresses_has_no_default_country():
    form = SinglePageAddressForm()
    assert form.fields["country"].initial is None


@override_settings(SHOOP_ADDRESS_HOME_COUNTRY="FI")
def test_checkout_singlepage_addresses_has_default_country():
    form = SinglePageAddressForm()
    assert form.fields["country"].initial == "FI"
