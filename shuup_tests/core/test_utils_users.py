# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import (
    CompanyContact, get_company_contact, get_company_contact_for_shop_staff,
    get_person_contact, PersonContact
)
from shuup.core.utils.users import (
    force_anonymous_contact_for_user, force_person_contact_for_user,
    is_user_all_seeing, toggle_all_seeing_for_user
)
from shuup.testing import factories


@pytest.mark.django_db
def test_is_user_all_seeing(rf, admin_user):
    assert not is_user_all_seeing(admin_user)
    toggle_all_seeing_for_user(admin_user)
    assert is_user_all_seeing(admin_user)
    toggle_all_seeing_for_user(admin_user)
    assert not is_user_all_seeing(admin_user)


@pytest.mark.django_db
def test_forcing_to_anonymous_contact(rf, admin_user):
    person_contact = get_person_contact(admin_user)
    assert person_contact is not None
    assert not get_person_contact(admin_user).is_anonymous

    company_contact = get_company_contact(admin_user)
    assert company_contact is None

    force_anonymous_contact_for_user(admin_user)
    assert get_person_contact(admin_user).is_anonymous

    force_anonymous_contact_for_user(admin_user, False)
    assert not get_person_contact(admin_user).is_anonymous
    assert get_person_contact(admin_user).user.id == admin_user.id


@pytest.mark.django_db
def test_company_contact_for_shop_staff(rf, admin_user):
    company_contact = get_company_contact(admin_user)
    assert company_contact is None

    shop = factories.get_default_shop()
    # Let's create shop for the shop staff
    company_contact = get_company_contact_for_shop_staff(shop, admin_user)

    company_contact = get_company_contact_for_shop_staff(shop, admin_user)
    assert company_contact is not None

    # Let's create second staff member to make sure all good with
    # creating company contact for shop staff.
    new_staff_user = factories.create_random_user()
    with pytest.raises(AssertionError):
        get_company_contact_for_shop_staff(shop, new_staff_user)

    new_staff_user.is_staff = True
    new_staff_user.save()
    
    with pytest.raises(AssertionError):
        # Since the new staff is not in shop members. The admin user
        # passed since he is also superuser.
        get_company_contact_for_shop_staff(shop, new_staff_user)

    shop.staff_members.add(new_staff_user)
    assert company_contact == get_company_contact_for_shop_staff(shop, new_staff_user)

    # Make sure both user has person contact linked to the company contact
    company_members = company_contact.members.all()
    assert get_person_contact(admin_user) in company_members
    assert get_person_contact(new_staff_user) in company_members


@pytest.mark.django_db
def test_forcing_to_person_contact(rf, admin_user):
    company_contact = get_company_contact(admin_user)
    assert company_contact is None
    shop = factories.get_default_shop()
    company_contact = get_company_contact_for_shop_staff(shop, admin_user)
    assert isinstance(company_contact, CompanyContact)
    assert company_contact == get_company_contact(admin_user)
    
    person_contact = get_person_contact(admin_user)
    assert person_contact is not None

    force_person_contact_for_user(admin_user)
    assert get_company_contact(admin_user) is None

    force_person_contact_for_user(admin_user, False)
    assert company_contact == get_company_contact(admin_user)


@pytest.mark.django_db
def test_forcing_to_person_and_anonymous_contact(rf, admin_user):
    company_contact = get_company_contact(admin_user)
    assert company_contact is None
    shop = factories.get_default_shop()
    company_contact = get_company_contact_for_shop_staff(shop, admin_user)
    assert isinstance(company_contact, CompanyContact)
    assert company_contact == get_company_contact(admin_user)

    person_contact = get_person_contact(admin_user)
    assert person_contact is not None
    assert not person_contact.is_anonymous

    force_person_contact_for_user(admin_user)
    assert get_company_contact(admin_user) is None

    force_anonymous_contact_for_user(admin_user)
    assert get_person_contact(admin_user).is_anonymous

    force_person_contact_for_user(admin_user, False)
    assert get_company_contact(admin_user) is None  # Since the person contact is still anonymous
    assert get_person_contact(admin_user).is_anonymous

    force_anonymous_contact_for_user(admin_user, False)
    assert company_contact == get_company_contact(admin_user)
    assert not get_person_contact(admin_user).is_anonymous
