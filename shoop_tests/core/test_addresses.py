# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ValidationError
from django.forms.models import modelform_factory
from django.test import override_settings
from django.utils.translation import override
import pytest
from shoop.core.excs import ImmutabilityError
from shoop.core.models import Address, SavedAddress, CompanyContact
from shoop.core.models.contacts import get_person_contact
from shoop.testing.factories import get_address, DEFAULT_ADDRESS_DATA
from shoop.utils.models import get_data_dict
import six


def test_partial_address_fails():
    address = Address(
        name=u"Dog Hello"
    )
    with pytest.raises(ValidationError):
        address.full_clean()


def test_basic_address():
    address = get_address()
    address.full_clean()
    string_repr = str(address)
    for field, value in get_data_dict(address).items():
        if field == "country":  # We can't test this right now, it's formatted in the repr
            continue
        if not value:
            continue
        assert value in string_repr, "Field %s is not represented in %r" % (field, string_repr)

    assert address.is_european_union, "Dog Fort, UK is in the EU"
    assert list(address.split_name) == ["Dog", "Hello"], "Names split correctly"
    assert address.first_name == "Dog", "Names split correctly"
    assert address.last_name == "Hello", "Names split correctly"
    assert address.full_name == "Sir Dog Hello , Esq.", "Names join correctly"


@pytest.mark.django_db
def test_address_saving_retrieving_and_immutability():
    # We can save an address...
    address = get_address()
    address.save()
    # mutate it...
    address.name = u"Dog Hi"
    # Then set it as immutable...
    address.set_immutable()

    # We can find the immutable copy...
    found_address = Address.objects.try_get_exactly_like(address)
    assert found_address and found_address.pk == address.pk, "Can't find the address we just saved :("

    # And when we try to save it again, it fails...
    address.name = u"Dog Yo"
    with pytest.raises(ImmutabilityError):
        address.save()

    # We can find the immutable copy, even if we've now changed a field...
    found_address = Address.objects.try_get_exactly_like(address, ignore_fields=("name",))
    assert found_address and found_address.pk == address.pk, "Can't find the address we just saved :("

    # But to mutate the address, we can copy it...
    address_copy = address.copy()
    assert not address_copy.pk
    address_copy.save()
    assert address_copy.pk != address.pk, "new address was saved as another entity"
    assert not address_copy.is_immutable, "new address is still mutable"


@pytest.mark.django_db
def test_address_ownership(admin_user):
    address = get_address()
    address.save()
    saved = SavedAddress(address=address)
    saved.owner = get_person_contact(admin_user)
    assert saved.get_title(), u"get_title does what it should even if there is no explicit title"
    saved.title = u"My favorite address"
    assert saved.get_title() == saved.title, u"get_title does what it should when there is an explicit title"
    assert six.text_type(saved) == saved.get_title(), u"str() is an alias for .get_title()"
    saved.full_clean()
    saved.save()
    assert SavedAddress.objects.for_owner(get_person_contact(admin_user)).filter(address=address).exists(), \
        "contacts can save addresses"
    assert SavedAddress.objects.for_owner(None).count() == 0, "Ownerless saved addresses aren't a real thing"


@pytest.mark.django_db
def test_address_form():
    form = modelform_factory(Address, exclude=())(data=DEFAULT_ADDRESS_DATA)
    company = CompanyContact(name=u"Doge Ltd", tax_number="1000-1000")
    address = Address.objects.from_address_form(form, company=company)
    assert address.company == company.name, "Company name was copied correctly"
    assert address.tax_number == company.tax_number, "Tax number was copied correctly"


def test_home_country_in_address():
    with override("fi"):
        finnish_address = Address(country="FI")
        with override_settings(SHOOP_ADDRESS_HOME_COUNTRY="US"):
            assert "Suomi" in str(finnish_address), "When home is not Finland, Finland appears in address string"
        with override_settings(SHOOP_ADDRESS_HOME_COUNTRY="FI"):
            assert "Suomi" not in str(finnish_address), "When home is Finland, Finland does not appear in address string"
