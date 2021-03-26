# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from shuup import configuration
from shuup.core.models import (
    AnonymousContact,
    CompanyContact,
    ContactGroup,
    ContactGroupPriceDisplay,
    PersonContact,
    get_company_contact,
    get_person_contact,
    get_price_display_for_group_and_shop,
    get_price_display_options_for_group_and_shop,
)
from shuup.core.pricing import PriceDisplayOptions
from shuup.testing.factories import create_random_company, get_all_seeing_key, get_default_shop, get_shop
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_omniscience(admin_user, regular_user):
    assert not get_person_contact(admin_user).is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), True)
    assert get_person_contact(admin_user).is_all_seeing
    assert not get_person_contact(regular_user).is_all_seeing
    assert not get_person_contact(None).is_all_seeing
    assert not get_person_contact(AnonymousUser()).is_all_seeing
    assert not AnonymousContact().is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), False)


@pytest.mark.django_db
def test_anonymity(admin_user, regular_user):
    assert not get_person_contact(admin_user).is_anonymous
    assert not get_person_contact(regular_user).is_anonymous
    assert get_person_contact(None).is_anonymous
    assert get_person_contact(AnonymousUser()).is_anonymous
    assert AnonymousContact().is_anonymous


@pytest.mark.django_db
def test_anonymous_contact():
    a1 = AnonymousContact()
    a2 = AnonymousContact()

    # Basic Contact stuff
    assert a1.is_anonymous, "AnonymousContact is anonymous"
    assert not a1.is_all_seeing, "AnonymousContact is not all seeing"
    assert a1.identifier is None
    assert a1.is_active, "AnonymousContact is active"
    assert a1.language == ""
    assert a1.marketing_permission is False
    assert a1.phone == ""
    assert a1.www == ""
    assert a1.timezone is None
    assert a1.prefix == ""
    assert a1.name == "", "AnonymousContact has no name"
    assert a1.suffix == ""
    assert a1.name_ext == ""
    assert a1.email == "", "AnonymousContact has no email"
    assert str(a1) == ""

    # Primary key / id
    assert a1.pk is None
    assert a1.id is None

    # AnonymousContact instance evaluates as false
    assert not a1

    # All AnonymousContacts should be equal
    assert a1 == a2

    # Cannot be saved
    with pytest.raises(NotImplementedError):
        a1.save()

    # Cannot be deleted
    with pytest.raises(NotImplementedError):
        a1.delete()

    assert isinstance(a1.groups, QuerySet)
    assert a1.groups.first().identifier == AnonymousContact.default_contact_group_identifier
    assert a1.groups.count() == 1
    assert len(a1.groups.all()) == 1


@pytest.mark.django_db
def test_anonymous_contact_vs_person(regular_user):
    anon = AnonymousContact()
    person = get_person_contact(regular_user)
    assert anon != person
    assert person != anon


@pytest.mark.django_db
def test_person_contact_creating_from_user(regular_user):
    user = regular_user
    user.first_name = "Joe"
    user.last_name = "Regular"

    # Preconditions
    assert user.get_full_name()
    assert not PersonContact.objects.filter(user=user).exists()

    # Actual test
    person = get_person_contact(user)
    assert person.is_active == user.is_active
    assert person.name == user.get_full_name()
    assert person.email == user.email


@pytest.mark.django_db
def test_person_name_init_by_name():
    john = PersonContact(name="John Smith")
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_person_name_create_with_name():
    john = PersonContact.objects.create(name="John Smith")
    assert PersonContact.objects.get(pk=john.pk).name == "John Smith"
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_person_name_init_by_first_and_last_name():
    john = PersonContact(first_name="John", last_name="Smith")
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_company_contact_name_ext():
    company = CompanyContact(name="TestCompany")
    assert company.name == "TestCompany"
    assert company.full_name == "TestCompany"
    company.name_ext = "California"
    company.save()
    assert company.name == "TestCompany"
    assert company.full_name == "TestCompany / California"


@pytest.mark.django_db
def test_person_name_gets_saved():
    john = PersonContact.objects.create(first_name="John", last_name="Smith")
    assert john.name == "John Smith"
    assert john in set(PersonContact.objects.filter(name="John Smith"))
    john.last_name = "Doe"
    assert john.name == "John Doe"
    john.save()
    assert john.name == "John Doe"
    assert john in set(PersonContact.objects.filter(name="John Doe"))
    assert john not in set(PersonContact.objects.filter(name="John Smith"))


def test_contact_group_repr_and_str_no_identifier_no_name():
    cg = ContactGroup()
    assert repr(cg) == "<ContactGroup:None>"
    assert str(cg) == "contact group"


def test_contact_group_repr_and_str_has_identifier_no_name():
    cg = ContactGroup(identifier="hello")
    assert repr(cg) == "<ContactGroup:None-hello>"
    assert str(cg) == 'contact group "hello"'


def test_contact_group_repr_and_str_no_identifier_has_name():
    cg = ContactGroup(name="world")
    assert repr(cg) == "<ContactGroup:None>"
    assert str(cg) == "world"


def test_contact_group_repr_and_str_has_identifier_has_name():
    cg = ContactGroup(identifier="hello", name="world")
    assert repr(cg) == "<ContactGroup:None-hello>"
    assert str(cg) == "world"


@pytest.mark.django_db
def test_default_anonymous_contact_group_repr_and_str():
    adg = AnonymousContact.get_default_group()
    assert repr(adg) == "<ContactGroup:%d-default_anonymous_group>" % adg.pk
    assert str(adg) == "Anonymous Contacts"


@pytest.mark.django_db
def test_default_company_contact_group_repr_and_str():
    cdg = CompanyContact.get_default_group()
    assert repr(cdg) == "<ContactGroup:%d-default_company_group>" % cdg.pk
    assert str(cdg) == "Company Contacts"


@pytest.mark.django_db
def test_default_person_contact_group_repr_and_str():
    pdg = PersonContact.get_default_group()
    assert repr(pdg) == "<ContactGroup:%d-default_person_group>" % pdg.pk
    assert str(pdg) == "Person Contacts"


@pytest.mark.django_db
def test_contact_group_price_display_options_filtering():
    shop = get_default_shop()
    cg0 = ContactGroup.objects.create(shop=shop)
    cg1 = ContactGroup.objects.create(shop=shop).set_price_display_options(hide_prices=True)
    cg2 = ContactGroup.objects.create(shop=shop).set_price_display_options(hide_prices=False)
    cg3 = ContactGroup.objects.create(shop=shop).set_price_display_options(show_prices_including_taxes=True)
    cg4 = ContactGroup.objects.create(shop=shop).set_price_display_options(show_prices_including_taxes=False)
    groups_qs = ContactGroup.objects.with_price_display_options(shop)
    assert isinstance(groups_qs, QuerySet)
    groups = list(groups_qs)
    assert cg0 not in groups
    assert cg1 in groups
    assert cg2 in groups
    assert cg3 in groups
    assert cg4 in groups


def test_contact_group_price_display_options_defaults():
    options = ContactGroup().get_price_display_options()
    assert isinstance(options, PriceDisplayOptions)
    assert options.include_taxes is None
    assert options.show_prices is True


@pytest.mark.parametrize("taxes", [True, False, None])
@pytest.mark.parametrize("hide_prices", [True, False, None])
def test_contact_group_price_display_options_defined(taxes, hide_prices):
    shop = get_default_shop()
    options = (
        ContactGroup.objects.create(shop=shop)
        .set_price_display_options(show_prices_including_taxes=taxes, hide_prices=hide_prices)
        .get_price_display_options()
    )
    assert isinstance(options, PriceDisplayOptions)
    assert options.include_taxes is taxes
    assert options.hide_prices is bool(hide_prices)
    assert options.show_prices is bool(not hide_prices)


@pytest.mark.django_db
def test_contact_group_price_display_for_contact(regular_user):
    shop = get_default_shop()
    group = ContactGroup.objects.create(shop=shop).set_price_display_options(hide_prices=True)
    person = get_person_contact(regular_user)
    person.groups.add(group)

    assert not person.in_shop(shop)

    # price options for non shop
    options = person.get_price_display_options(group=group)
    assert options
    assert options.show_prices is True  # True by default
    assert options.include_taxes is None  # again, a default

    # price options for the shop
    options = person.get_price_display_options(group=group, shop=shop)
    assert options
    assert options.show_prices is False
    assert options.include_taxes is None

    default_group = person.get_default_group()
    assert default_group.pk != group.pk
    assert default_group.price_display_options.exists()

    options = person.get_price_display_options(group=default_group)
    assert options
    assert options.show_prices is True  # True by default
    assert options.include_taxes is None

    options = person.get_price_display_options(group=default_group, shop=shop)
    assert options
    assert options.show_prices is True  # True by default
    assert options.include_taxes is None

    options = get_price_display_options_for_group_and_shop(group, None)
    assert options
    assert options.show_prices is True
    assert options.include_taxes is None

    options = get_price_display_options_for_group_and_shop(group, shop)
    assert options
    assert options.show_prices is False
    assert options.include_taxes is None

    # this will create options as well
    options = default_group.price_display_options.for_group_and_shop(default_group, shop)
    assert options
    options.show_prices_including_taxes = True
    options.save()

    # Now since default group has pricing options set these should be returned
    default_options = person.get_price_display_options()
    assert not default_options.include_taxes
    assert not default_options.hide_prices

    # change default group
    default_group.set_price_display_options(hide_prices=True)
    options = person.get_price_display_options(group=default_group)
    assert options
    assert options.show_prices is False  # True by default
    assert options.include_taxes is None


@pytest.mark.django_db
def test_get_company_contact(regular_user):
    person_contact = get_person_contact(regular_user)
    assert person_contact != AnonymousContact()
    assert not get_company_contact(regular_user)

    company_contact = create_random_company()
    company_contact.members.add(person_contact)
    assert get_company_contact(regular_user) == company_contact


@pytest.mark.django_db
def test_contact_in_shop(regular_user):
    shop = get_default_shop()
    contact = get_person_contact(regular_user)

    assert not contact.in_shop(shop)
    assert not contact.shops.exists()

    contact.add_to_shop(shop)
    assert contact.shops.count() == 1
    assert contact.in_shop(shop)
    assert contact.in_shop(shop, only_registration=True)

    shop2 = get_shop()

    assert shop.pk != shop2.pk
    assert not contact.in_shop(shop2)
    assert not contact.in_shop(shop2, only_registration=True)

    contact.add_to_shop(shop2)
    assert contact.shops.count() == 2
    assert contact.in_shop(shop)
    assert contact.in_shop(shop, only_registration=True)
    assert contact.in_shop(shop2)
    assert not contact.in_shop(shop2, only_registration=True)


@pytest.mark.django_db
def test_contact_in_shops(regular_user):
    shop1 = get_default_shop()
    shop2 = get_shop(identifier="shop-2")
    shop3 = get_shop(identifier="shop-3")
    contact = get_person_contact(regular_user)

    all_shop_ids = [shop1.pk, shop2.pk, shop3.pk]

    contact.add_to_shops(shop1, [shop2, shop3])

    assert contact.registered_in(shop1)
    assert not contact.registered_in(shop2)
    assert not contact.registered_in(shop3)
    assert contact.in_shop(shop1)
    assert contact.in_shop(shop2)
    assert contact.in_shop(shop3)
    assert contact.shops.filter(pk__in=all_shop_ids).count() == len(all_shop_ids)

    contact.add_to_shops(shop2, [shop1, shop3])
    assert contact.registered_in(shop1)
    assert not contact.registered_in(shop2)
    assert not contact.registered_in(shop3)
    assert contact.in_shop(shop1)
    assert contact.in_shop(shop2)
    assert contact.in_shop(shop3)
    assert contact.shops.filter(pk__in=all_shop_ids).count() == len(all_shop_ids)

    contact.registration_shop = None
    contact.shops.clear()
    contact.save()

    contact.add_to_shops(shop2, [shop1, shop3])
    assert not contact.registered_in(shop1)
    assert contact.registered_in(shop2)
    assert not contact.registered_in(shop3)
    assert contact.in_shop(shop1)
    assert contact.in_shop(shop2)
    assert contact.in_shop(shop3)
    assert contact.shops.filter(pk__in=all_shop_ids).count() == len(all_shop_ids)


@pytest.mark.django_db
def test_cannot_add_shop(regular_user):
    shop = get_default_shop()
    contact = get_person_contact(regular_user)
    group = contact.get_default_group()

    assert not group.shop

    group.shop = shop
    with pytest.raises(ValidationError):
        group.save()


@pytest.mark.django_db
def test_price_displays(regular_user):
    shop = get_default_shop()
    cg = ContactGroup.objects.create(shop=shop).set_price_display_options(hide_prices=True)
    assert isinstance(cg, ContactGroup)

    assert ContactGroupPriceDisplay.objects.count() == 1
    kk = ContactGroupPriceDisplay.objects.first()

    obj = cg.price_display_options.for_group_and_shop(cg, shop)
    assert kk == obj
    assert obj.show_prices_including_taxes is None
    assert obj.hide_prices is True
    assert obj.show_pricing is True

    obj2 = get_price_display_for_group_and_shop(cg, shop)
    assert obj2 == obj

    options = cg.get_price_display_options()

    assert not options.show_prices

    obj = cg.price_display_options.for_group_and_shop(cg, shop)
    obj.hide_prices = False
    obj.save()
    options = cg.get_price_display_options()
    assert options.show_prices


@pytest.mark.django_db
def test_contact_options():
    contact = PersonContact.objects.create(name="randon name")
    contact.options = dict(var=1, xpto=2)
    contact.save()

    contact = PersonContact.objects.get(pk=contact.pk)
    assert isinstance(contact.options, dict)
    assert contact.options["var"] == 1
    assert contact.options["xpto"] == 2

    contact = PersonContact.objects.get(pk=contact.pk)
    contact.options["vaca"] = "cow"
    contact.save()

    contact = PersonContact.objects.get(pk=contact.pk)
    assert isinstance(contact.options, dict)
    assert contact.options["vaca"] == "cow"
