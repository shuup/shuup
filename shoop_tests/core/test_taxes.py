# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.translation import activate

from shoop.core.models import CustomerTaxGroup


@pytest.mark.django_db
def test_customertaxgroup():
    activate("en")
    person_group = CustomerTaxGroup.get_default_person_group()
    assert CustomerTaxGroup.objects.count() == 1
    assert person_group.identifier == "default_person_customers"
    assert person_group.name == "Retail Customers"

    company_group = CustomerTaxGroup.get_default_company_group()
    assert CustomerTaxGroup.objects.count() == 2
    assert company_group.identifier == "default_company_customers"
    assert company_group.name == "Company Customers"
