# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AnonymousUser


def is_admin_user(request):
    user = getattr(request, "user", AnonymousUser())
    shop = getattr(request, "shop", None)
    if not (user and shop):
        return False

    if getattr(user, 'is_superuser', False):
        return True

    return bool(getattr(user, 'is_staff', False) and shop.staff_members.filter(id=user.id).exists())
