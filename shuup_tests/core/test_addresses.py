# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.translation import override

from shuup.core.models import ImmutableAddress, MutableAddress, SavedAddress, get_person_contact
from shuup.testing.factories import get_address
from shuup.utils.models import get_data_dict


def test_partial_address_fails():
    address = MutableAddress(name=u"Dog Hello")
    with pytest.raises(ValidationError):
        address.full_clean()


@pytest.mark.django_db
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

    assert address.is_european_union, "Dog Fort, UK is not in the EU, France actually is"
    assert list(address.split_name) == ["Dog", "Hello"], "Names split correctly"
    assert address.first_name == "Dog", "Names split correctly"
    assert address.last_name == "Hello", "Names split correctly"
    assert address.full_name == "Sir Dog Hello , Esq.", "Names join correctly"


@pytest.mark.django_db
def test_uk_not_in_eu():
    address = get_address(country="GB")
    assert not address.is_european_union


@pytest.mark.django_db
def test_address_saving_retrieving_and_immutability():
    # We can save an address...
    address = get_address()
    address.save()
    # mutate it...
    address.name = u"Dog Hi"
    # Then set it as immutable...
    immutable_address = address.to_immutable()
    immutable_address.save()

    # And when we try to save it again, it fails...
    immutable_address.name = u"Dog Yo"
    with pytest.raises(ValidationError):
        immutable_address.save()

    # But to mutate the address, we can copy it...
    address_copy = address.to_mutable()
    assert not address_copy.pk
    address_copy.save()
    assert address_copy.pk != address.pk, "new address was saved as another entity"


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
    assert (
        SavedAddress.objects.for_owner(get_person_contact(admin_user)).filter(address=address).exists()
    ), "contacts can save addresses"
    assert SavedAddress.objects.for_owner(None).count() == 0, "Ownerless saved addresses aren't a real thing"


def test_home_country_in_address():
    with override("fi"):
        finnish_address = MutableAddress(country="FI")
        with override_settings(SHUUP_ADDRESS_HOME_COUNTRY="US"):
            assert "Suomi" in str(finnish_address), "When home is not Finland, Finland appears in address string"
        with override_settings(SHUUP_ADDRESS_HOME_COUNTRY="FI"):
            assert "Suomi" not in str(
                finnish_address
            ), "When home is Finland, Finland does not appear in address string"


@pytest.mark.django_db
def test_immutable_addresses_from_data():
    test_data = {
        "name": "Test name",
        "street": "Test street",
        "postal_code": "1234567",
        "city": "Test city",
        "country": "US",
    }
    immutable_address = ImmutableAddress.from_data(test_data)
    test_data.pop("postal_code")
    # Since test_data does not include postal code from_data should not return same ImmutableAddress as before
    new_immutable_address = ImmutableAddress.from_data(test_data)
    assert immutable_address != new_immutable_address


@pytest.mark.django_db
def test_immutable_address():
    address = get_address()
    new_immutable = address.to_immutable()

    # New address should be saved
    assert new_immutable.pk is not None
    assert isinstance(new_immutable, ImmutableAddress)
    assert get_data_dict(address).items() == get_data_dict(new_immutable).items()

    # Taking immutable for same address should return same object
    assert new_immutable == address.to_immutable()

    # Taking immutable from new_immutable should return same item
    assert new_immutable == new_immutable.to_immutable()


def test_new_mutable_address():
    address = get_address()
    new_mutable = address.to_mutable()

    # New address should be unsaved
    assert new_mutable.pk is None
    assert isinstance(new_mutable, MutableAddress)
    assert get_data_dict(address).items() == get_data_dict(new_mutable).items()
