# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from .detail import UserDetailView
from .list import UserListView
from .password import UserChangePasswordView, UserResetPasswordView
from .permissions import UserChangePermissionsView

__all__ = [
    "UserListView",
    "UserDetailView",
    "UserChangePasswordView",
    "UserResetPasswordView",
    "UserChangePermissionsView",
]
