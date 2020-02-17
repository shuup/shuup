# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shuup.core.models import SavedAddress
from django.db.utils import IntegrityError


@pytest.mark.django_db
def test_fk_constraint():
    """
    Test that FK constraint should be on and objects MUST exist
    """
    with pytest.raises(IntegrityError):
        SavedAddress.objects.create(owner_id=78472384723847218, address_id=4723847283)
