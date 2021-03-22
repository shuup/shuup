# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
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
    permissions = set()

    def has_perm(self, perm):
        return self.is_superuser or (perm in self.permissions)


class SuperUser(StaffUser):
    is_superuser = True

    def has_perm(self, perm, obj=None):
        return True
