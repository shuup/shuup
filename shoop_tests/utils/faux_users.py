# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AnonymousUser

__all__ = ["AnonymousUser", "StaffUser", "SuperUser", "AuthenticatedUser"]

class AuthenticatedUser(AnonymousUser):
    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

class StaffUser(AuthenticatedUser):
    is_staff = True

class SuperUser(StaffUser):
    is_superuser = True

    def has_perm(self, perm, obj=None):
        return True
