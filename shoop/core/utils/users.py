# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.contrib.auth import get_user_model


def real_user_or_none(user):
    """
    Convert anonymous user to None.

    If user is anonymous, return None, otherwise return the user as is.
    """
    assert (user is None or user.is_anonymous() or
            isinstance(user, get_user_model()))
    return user if (user and not user.is_anonymous()) else None
