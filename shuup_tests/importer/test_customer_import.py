# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import six
from django.utils.translation import activate

from shuup.core.models._addresses import MutableAddress
from shuup.default_importer.importers.contact import CompanyContactImporter, PersonContactImporter
from shuup.importer.transforms import transform_file
from shuup.importer.utils.importer import ImportMode
from shuup.testing.factories import get_default_shop


@pytest.mark.django_db
def test_customer_sample(rf):
    filename = "customer_sample.xlsx"
    activate("en")
    shop = get_default_shop()

    path = os.path.join(os.path.dirname(__file__), "data", "contact", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = PersonContactImporter(
        transformed_data, CompanyContactImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()
    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    contacts = importer.new_objects
    assert len(contacts) == 2

    assert MutableAddress.objects.count() == 2

    first_contact = contacts[0]
    second_contact = contacts[1]

    first_address = MutableAddress.objects.first()
    second_address = MutableAddress.objects.last()

    first_row = {
        "first_name": "Test",
        "last_name": "Tester",
        "email": "test@example.com",
        "street": "TestStreet",
        "city": "Los Angeles",
        "postal_code": "90000",
        "country": "US",
        "region_code": "CA",
        "phone": "1123555111",
    }
    second_row = {
        "first_name": "My",
        "last_name": "Sample",
        "email": "my-sample@example.com",
        "street": "my-sample",
        "city": "Los Angeles",
        "postal_code": "90001",
        "country": "US",
        "region_code": "CA",
        "phone": "1235678900",
    }
    assert_contact_address(first_contact, first_address, first_row)
    assert_contact_address(second_contact, second_address, second_row)


@pytest.mark.django_db
def test_company_sample(rf):
    filename = "company_contact_sample.xlsx"
    activate("en")
    shop = get_default_shop()

    path = os.path.join(os.path.dirname(__file__), "data", "contact", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = CompanyContactImporter(
        transformed_data, CompanyContactImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()
    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    contacts = importer.new_objects

    assert len(contacts) == 2

    assert MutableAddress.objects.count() == 2

    first_contact = contacts[0]
    second_contact = contacts[1]

    first_address = MutableAddress.objects.first()
    second_address = MutableAddress.objects.last()

    first_row = {
        "name": "Test Company",
        "name_ext": "Packaging Section",
        "tax_number": "1234567-888",
        "email": "test@example.com",
        "street": "TestStreet",
        "city": "Los Angeles",
        "postal_code": "90000",
        "country": "US",
        "region_code": "CA",
        "phone": "1123555111",
    }
    second_row = {
        "name": "Test Company 2",
        "name_ext": "",
        "tax_number": "12333-2232",
        "email": "test-company@example.com",
        "street": "Test Company Street",
        "city": "Los Angeles",
        "postal_code": "90001",
        "country": "US",
        "region_code": "CA",
        "phone": "1235678900",
    }
    assert_contact_address(first_contact, first_address, first_row)
    assert_contact_address(second_contact, second_address, second_row)


def assert_contact_address(contact, address, row):
    assert contact.default_shipping_address == address
    assert contact.default_billing_address == address

    assert address.name == contact.name
    assert address.email == contact.email

    for k, v in six.iteritems(row):
        if hasattr(address, k):
            assert getattr(address, k) == v
        if hasattr(contact, k):
            assert getattr(contact, k) == v
