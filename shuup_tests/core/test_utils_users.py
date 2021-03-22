# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.utils.users import is_user_all_seeing, toggle_all_seeing_for_user


@pytest.mark.django_db
def test_is_user_all_seeing(rf, admin_user):
    assert not is_user_all_seeing(admin_user)
    toggle_all_seeing_for_user(admin_user)
    assert is_user_all_seeing(admin_user)
    toggle_all_seeing_for_user(admin_user)
    assert not is_user_all_seeing(admin_user)
