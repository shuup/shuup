# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model

from shuup.core.models import SavedAddress, get_company_contact, get_person_contact
from shuup.testing.factories import get_address, get_default_shop
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient
from shuup_tests.utils.fixtures import REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME, regular_user

User = get_user_model()

regular_user = regular_user  # noqa


def default_address_data():
    return {
        "saved_address-title": "Fakerr",
        "saved_address-role": "1",
        "saved_address-status": "1",
        "address-name": "Derpy Test",
        "address-street": "Derp-street",
        "address-city": "Los Angeles",
        "address-region_code": "CA",
        "address-postal_code": "90000",
        "address-country": "US",
    }


def initialize_test(regular_user, person=True):
    client = SmartClient()
    get_default_shop()
    if person:
        contact = get_person_contact(regular_user)
    else:
        contact = get_company_contact(regular_user)

    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    return client, contact


@pytest.mark.django_db
def test_addressbook_no_address(regular_user):
    client, contact = initialize_test(regular_user)

    addressbook_url = reverse("shuup:address_book")
    response, soup = client.response_and_soup(addressbook_url)
    assert not len(soup(text="Name:"))


@pytest.mark.django_db
def test_addressbook_has_addresses(regular_user):
    client, contact = initialize_test(regular_user)
    address = get_address()
    address.save()
    billing_name = address.name
    contact.default_billing_address = address
    contact.save()
    addressbook_url = reverse("shuup:address_book")
    soup = client.soup(addressbook_url)

    assert len(soup(text="Name:")) == 1
    elems = [p for p in soup.find_all("p") if p.text == "Name: %s" % billing_name]
    assert len(elems) == 1

    address = get_address(**{"name": "Kek Bur"})
    address.save()
    shipping_name = address.name
    contact.default_shipping_address = address
    contact.save()

    soup = client.soup(addressbook_url)

    elems = [p for p in soup.find_all("p") if p.text == "Name: %s" % billing_name]
    assert len(elems) == 1

    assert len(soup(text="Name:")) == 2
    elems = [p for p in soup.find_all("p") if p.text == "Name: %s" % shipping_name]
    assert len(elems) == 1


@pytest.mark.django_db
def test_addressbook_has_saved_addresses(regular_user):
    client, contact = initialize_test(regular_user)
    address = get_address()
    address.save()
    address_title = "TestAddress"
    sa = SavedAddress.objects.create(owner=contact, address=address, title=address_title)
    addressbook_url = reverse("shuup:address_book")

    soup = client.soup(addressbook_url)
    elems = [h for h in soup.find_all("h2") if h.text.strip() == address_title]
    assert len(elems) == 1
    assert len(soup(text="Name:")) == 1

    second_address_title = "TestAddress2"
    sa = SavedAddress.objects.create(owner=contact, address=address, title=second_address_title)
    soup = client.soup(addressbook_url)
    elems = [h for h in soup.find_all("h2") if h.text.strip() == second_address_title]
    assert len(elems) == 1
    assert len(soup(text="Name:")) == 2


@pytest.mark.django_db
def test_addressbook_addresses_create_and_edit(regular_user):
    client, contact = initialize_test(regular_user)

    new_address_url = reverse("shuup:address_book_new")
    soup = client.soup(new_address_url)

    data = default_address_data()
    response, soup = client.response_and_soup(new_address_url, data, "post")
    assert response.status_code == 302
    assert SavedAddress.objects.count() == 1
    assert SavedAddress.objects.first().owner == contact

    addressbook_url = reverse("shuup:address_book")
    soup = client.soup(addressbook_url)
    elems = [h for h in soup.find_all("h2") if h.text.strip() == data.get("saved_address-title")]
    assert len(elems) == 1
    assert len(soup(text="Name:")) == 1

    new_title = "Test Title"
    soup = client.soup(new_address_url)
    data.update({"saved_address-title": new_title})

    response, soup = client.response_and_soup(new_address_url, data, "post")
    assert response.status_code == 302
    assert SavedAddress.objects.count() == 2
    sa = SavedAddress.objects.last()
    assert sa.owner == contact
    assert sa.title == new_title

    soup = client.soup(addressbook_url)
    elems = [h for h in soup.find_all("h2") if h.text.strip() == new_title]
    assert len(elems) == 1
    assert len(soup(text="Name:")) == 2

    # edit old
    updated_title = "Updated Title"
    edit_url = reverse("shuup:address_book_edit", kwargs={"pk": sa.pk})
    soup = client.soup(edit_url)
    data.update({"saved_address-title": updated_title})

    response, soup = client.response_and_soup(edit_url, data, "post")
    assert response.status_code == 302
    assert SavedAddress.objects.count() == 2
    sa = SavedAddress.objects.last()
    assert sa.owner == contact
    assert sa.title == updated_title

    soup = client.soup(addressbook_url)
    elems = [h for h in soup.find_all("h2") if h.text.strip() == updated_title]
    assert len(elems) == 1
    assert len(soup(text="Name:")) == 2


@pytest.mark.django_db
def delete_address(regular_user):
    client, contact = initialize_test(regular_user)
    address = get_address()
    address.save()

    sa = SavedAddress.objects.create(owner=contact, address=address)
    delete_url = reverse("shuup:address_book_delete", kwargs={"pk": sa.pk})
    response, soup = client.response_and_soup(delete_url)
    assert response.status_code == 302
    assert "Cannot remove address" not in soup

    user = User.objects.create_user("john", "doe@example.com", "doepassword")
    contact2 = get_person_contact(user)
    address2 = get_address()
    address2.save()

    sa2 = SavedAddress.objects.create(owner=contact2, address=address2)
    response, soup = client.response_and_soup(delete_url)
    assert response.status_code == 302
    assert "Cannot remove address" in soup
