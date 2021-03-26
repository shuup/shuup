# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError

from shuup.core.models import (
    AnonymousContact,
    ContactGroup,
    ContactGroupPriceDisplay,
    PersonContact,
    get_person_contact,
    get_price_display_for_group_and_shop,
)
from shuup.core.pricing import PriceDisplayOptions
from shuup.testing.factories import get_default_shop, get_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import is_anonymous
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_contact_groups(rf, regular_user):
    shop = get_default_shop()

    assert ContactGroupPriceDisplay.objects.count() == 0
    request = apply_request_middleware(rf.get("/"))

    # default groups created for non shop and shop
    assert ContactGroupPriceDisplay.objects.count() == 2

    assert is_anonymous(request.user)
    user = request.user
    contact = get_person_contact(user)
    assert contact == AnonymousContact()

    group = contact.get_default_group()

    assert group.is_protected

    groups = ContactGroup.objects.all()
    assert groups.count() == 1
    assert not groups.filter(shop=shop).exists()
    assert groups.filter(shop__isnull=True).exists()

    group = groups.first()
    assert group.identifier == AnonymousContact.default_contact_group_identifier

    assert ContactGroupPriceDisplay.objects.count() == 2

    g1 = ContactGroupPriceDisplay.objects.first()
    assert g1.group == group
    assert not g1.shop

    assert group.price_display_options.exists()
    assert group.price_display_options.for_group_and_shop(group, shop) != group.price_display_options.first()
    assert ContactGroupPriceDisplay.objects.count() == 2  # new one was created (shop + anonymous)

    g2 = ContactGroupPriceDisplay.objects.exclude(id=g1.id).first()
    assert g2.group == group  # same group as before
    assert g2.shop == shop

    assert group.price_display_options.count() == 2

    for cgpd in ContactGroupPriceDisplay.objects.all():
        assert not cgpd.group.members.count()

    options = group.get_price_display_options()
    assert options

    # create real contact
    contact = get_person_contact(regular_user)
    assert contact.groups.count()  # contact was added to default group
    contact.add_to_shop(shop)
    group_with_shop = contact.get_default_group()
    assert contact.groups.first() == group_with_shop

    assert group_with_shop.identifier == PersonContact.default_contact_group_identifier
    assert ContactGroupPriceDisplay.objects.count() == 3  # new one was created

    g3 = ContactGroupPriceDisplay.objects.exclude(id__in=[g1.id, g2.id]).first()
    assert g3.group != group  # same group as before
    assert g3.group == group_with_shop
    assert not g3.shop  # no group as it's the default group

    groups = ContactGroup.objects.all()
    assert groups.count() == 2  # two groups
    assert not groups.filter(shop=shop).exists()  # still not exists as we are using defaults
    assert groups.filter(shop__isnull=True).count() == 2
    assert (
        groups.filter(
            identifier__in=[
                AnonymousContact.default_contact_group_identifier,
                PersonContact.default_contact_group_identifier,
            ]
        ).count()
        == 2
    )

    assert ContactGroupPriceDisplay.objects.count() == 3  # no new ones created

    assert group.price_display_options.count() == 2  # all in same group

    assert (
        group.price_display_options.for_group_and_shop(group_with_shop, shop) not in group.price_display_options.all()
    )

    assert ContactGroupPriceDisplay.objects.count() == 4  # new was created


@pytest.mark.django_db
def test_plain_contact_group():
    shop = get_default_shop()

    with pytest.raises(ValidationError) as exc_info:
        ContactGroup.objects.create(identifier=AnonymousContact.default_contact_group_identifier, shop=shop)
        assert exc_info.value == "Cannot set shop for default Contact Group."

    cg = ContactGroup.objects.create(identifier="test", shop=shop).set_price_display_options(hide_prices=True)
    assert isinstance(cg, ContactGroup)

    cg = ContactGroup.objects.create(identifier="test2", shop=shop)
    assert cg.price_display_options.exists()

    # remove options for tests sake...
    cg.price_display_options.all().delete()

    assert cg.get_price_display_options()  # yep, we still get something


@pytest.mark.django_db
def test_multishop(rf):
    shop1 = get_default_shop()
    shop2 = get_shop()
    assert shop1.pk != shop2.pk

    request = apply_request_middleware(rf.get("/"))
    assert is_anonymous(request.user)
    user = request.user
    contact = get_person_contact(user)
    assert contact == AnonymousContact()

    # both shops have anonymous groups
    group = contact.get_default_group()  # ensure default group exists

    grp1 = group.set_price_display_options(shop=shop1, hide_prices=False)
    assert grp1
    assert isinstance(grp1, ContactGroup)
    dspl1 = get_price_display_for_group_and_shop(group, shop1)
    assert isinstance(dspl1, ContactGroupPriceDisplay)
    assert not get_price_display_for_group_and_shop(group, shop2)

    # shop 2 decides to setup options
    grp2 = group.set_price_display_options(shop=shop2, hide_prices=True)
    assert grp1 == grp2  # returns same group
    assert isinstance(grp2, ContactGroup)
    dspl2 = get_price_display_for_group_and_shop(group, shop2)
    assert isinstance(dspl2, ContactGroupPriceDisplay)

    # get returns proper values
    opts11 = contact.get_price_display_options(shop=shop1)
    assert isinstance(opts11, PriceDisplayOptions)
    opts12 = contact.get_price_display_options(shop=shop2)
    assert isinstance(opts12, PriceDisplayOptions)

    assert opts11 != opts12
    assert opts11.show_prices != opts12.show_prices
