# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from rest_framework import permissions

from shuup import configuration


class PermissionLevel(object):
    """ Permissions set. The greater, the more restrective """
    PUBLIC_READ = 1
    PUBLIC_WRITE = 2
    AUTHENTICATED_READ = 3
    AUTHENTICATED_WRITE = 4
    ADMIN = 5
    DISABLED = 6


# the default permission if not set anywhere
DEFAULT_PERMISSION = PermissionLevel.ADMIN


def make_permission_config_key(view):
    """
    Generates the the key to be stored in configuration for a given view

    :type view: rest_framework.views.APIView
    """
    return "api_permission_{}".format(view.__class__.__name__)


class ShuupAPIPermission(permissions.BasePermission):
    """
    Shuup API Permissions.
    Permissions are configured through admin in a per-viewset scheme.
    Permissions levels are number based as it is faster to compare then strings.
    """

    def has_permission(self, request, view):
        try:
            permission = int(configuration.get(None, make_permission_config_key(view), DEFAULT_PERMISSION))
        except ValueError:
            permission = DEFAULT_PERMISSION

        # god mode - just works if API is not disabled
        if request.user.is_superuser:
            return (permission <= PermissionLevel.ADMIN)

        # safe requests: GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            # to READ, the permissions can be WRITE or READ
            return ((request.user.is_authenticated() and permission <= PermissionLevel.AUTHENTICATED_WRITE) or
                    permission <= PermissionLevel.PUBLIC_WRITE)

        # NOT safe: POST, PUT, DELETE
        else:
            # to change data, permission must be exactly WRITE
            if request.user.is_authenticated():
                return permission in (PermissionLevel.AUTHENTICATED_WRITE, PermissionLevel.PUBLIC_WRITE)
            return (permission == PermissionLevel.PUBLIC_WRITE)
