# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

REGULAR_USER_PASSWORD = "password"
REGULAR_USER_USERNAME = "regular-joe"
REGULAR_USER_EMAIL = "regular@shuup.local"


@pytest.fixture()
def regular_user(db, django_user_model, django_username_field):
    UserModel = django_user_model
    username_field = django_username_field

    try:
        return UserModel._default_manager.get(**{username_field: REGULAR_USER_USERNAME})
    except UserModel.DoesNotExist:
        kwargs = {"email": REGULAR_USER_EMAIL, "password": REGULAR_USER_PASSWORD, username_field: REGULAR_USER_USERNAME}

        return UserModel._default_manager.create_user(**kwargs)
