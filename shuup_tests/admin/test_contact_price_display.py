# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from bs4 import BeautifulSoup
from django.utils.encoding import force_text

from shuup.admin.modules.contact_group_price_display.views import ContactGroupPriceDisplayEditView
from shuup.admin.modules.contact_group_price_display.views.forms import PriceDisplayChoices
from shuup.core.models import (
    AnonymousContact,
    CompanyContact,
    ContactGroup,
    ContactGroupPriceDisplay,
    PersonContact,
    get_groups_for_price_display_create,
    get_person_contact,
    get_price_display_options_for_group_and_shop,
    get_price_displays_for_shop,
)
from shuup.core.models._contacts import PROTECTED_CONTACT_GROUP_IDENTIFIERS
from shuup.testing.factories import get_default_customer_group, get_default_shop
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_display_queryset(regular_user):
    shop = get_default_shop()
    anonymous_group = AnonymousContact().get_default_group()
    PersonContact().get_default_group()
    CompanyContact().get_default_group()
    assert get_groups_for_price_display_create(shop).count() == 3
    assert get_price_displays_for_shop(None).count() == 3
    assert get_price_displays_for_shop(shop).count() == 3

    get_person_contact(regular_user)

    assert get_price_displays_for_shop(shop).count() == 3

    # create new group display (from admin usually)
    ContactGroupPriceDisplay.objects.create(group=anonymous_group, shop=shop)

    for_create = get_groups_for_price_display_create(shop)
    assert for_create.count() == 2
    assert anonymous_group not in for_create

    items = get_price_displays_for_shop(shop)
    assert items.count() == 3
    for item in items:
        if item.group == anonymous_group:
            assert item.shop
        else:
            assert not item.shop
        assert item.group.identifier in PROTECTED_CONTACT_GROUP_IDENTIFIERS

    new_group = ContactGroup.objects.create(identifier="test", shop=shop)

    items = get_price_displays_for_shop(shop)
    assert items.count() == 4
    for item in items:
        if item.group in [new_group, anonymous_group]:
            assert item.shop
        else:
            assert not item.shop
        if item.group != new_group:
            assert item.group.identifier in PROTECTED_CONTACT_GROUP_IDENTIFIERS
        else:
            assert item.group.identifier == "test"


@pytest.mark.django_db
def test_admin_edit(rf, admin_user):
    shop = get_default_shop()

    group = get_default_customer_group(shop)
    cgpd = ContactGroupPriceDisplay.objects.for_group_and_shop(group, shop)
    view = ContactGroupPriceDisplayEditView.as_view()

    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options.show_prices

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=cgpd.pk)
    response.render()
    content = force_text(response.content)

    data = extract_form_fields(BeautifulSoup(content))

    data.update(
        {
            "price_display_mode": [PriceDisplayChoices.HIDE.value],
            "group": group.id,
        }
    )

    request = apply_request_middleware(rf.post("/", data), user=admin_user, shop=shop)
    response = view(request, pk=cgpd.pk)
    assert response.status_code == 302  # save successful

    group = get_default_customer_group(shop)

    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options.show_prices is False
    assert options.include_taxes is None

    # none, with_taxes, without_taxes, hide
    k = "price_display_mode"
    data.update({k: [PriceDisplayChoices.NONE.value]})
    request = apply_request_middleware(rf.post("/", data), user=admin_user, shop=shop)
    response = view(request, pk=cgpd.pk)
    assert response.status_code == 302  # save successful

    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options.show_prices is True  # default
    assert options.include_taxes is None

    data.update({k: [PriceDisplayChoices.WITH_TAXES.value]})
    request = apply_request_middleware(rf.post("/", data), user=admin_user, shop=shop)
    response = view(request, pk=cgpd.pk)
    assert response.status_code == 302  # save successful
    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options.show_prices is True  # default
    assert options.include_taxes is True

    data.update({k: [PriceDisplayChoices.WITHOUT_TAXES.value]})
    request = apply_request_middleware(rf.post("/", data), user=admin_user, shop=shop)
    response = view(request, pk=cgpd.pk)
    assert response.status_code == 302  # save successful

    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options.show_prices is True
    assert options.include_taxes is False
