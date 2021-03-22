# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.db.models import ProtectedError

from shuup.core.models import AnonymousContact, ContactGroup
from shuup.testing.factories import create_random_company, create_random_person, get_default_customer_group


@pytest.mark.django_db
@pytest.mark.parametrize("contact", [AnonymousContact, create_random_company, create_random_person])
def test_protected_default_groups(contact):
    protected_group = contact().get_default_group()
    assert not protected_group.can_delete()
    with pytest.raises(ProtectedError):
        protected_group.delete()


@pytest.mark.django_db
def test_contact_group_delete():
    default_group = get_default_customer_group()
    group_count = ContactGroup.objects.count()
    default_group.delete()
    assert ContactGroup.objects.count() == (group_count - 1)
