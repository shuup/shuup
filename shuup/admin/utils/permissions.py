# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import Permission


def get_default_model_permissions(model):
    """
    Return a set of all default permissions for a given model.

    :param model: Model class
    :type model: django.db.Model
    :return: Set of default model permissions as strings
    :rtype: set[str]
    """
    permissions = set()

    for default in model._meta.default_permissions:
        permissions.add("%s.%s_%s" % (model._meta.app_label, default, model._meta.model_name))

    return permissions


def get_missing_permissions(user, permissions):
    """
    Return a set of missing permissions for a given iterable of
    permission strings.

    :param user: User instance to check for permissions
    :type user: django.contrib.auth.models.User
    :param permissions: Iterable of permission strings
    :type permissions: Iterable[str]
    :return: Set of missing permission strings
    :rtype: set[str]
    """
    if callable(getattr(user, 'has_perm', None)):
        missing_permissions = set(p for p in set(permissions) if not user.has_perm(p))
    else:
        missing_permissions = set(permissions)

    return missing_permissions


def get_permissions_from_urls(urls):
    """
    Return a set of permissions for a given iterable of urls.

    :param urls: Iterable of url objects to check for permissions
    :type urls: Iterable[django.core.urlresolvers.RegexURLPattern]
    :return: Set of permissions for urls as strings
    :rtype: set[str]
    """
    permissions = set()
    for url in urls:
        if hasattr(url, "permissions") and url.permissions:
            permissions.update(url.permissions)

    return permissions


def get_permission_object_from_string(permission_string):
    """
    Given a permission string of the form `app_label.permission_string`,
    get actual permission object.

    :param permission_string: Permission string
    :type permission_strings: str
    :return: Permission object
    :rtype: django.contrib.auth.models.Permission
    """
    app_label, codename = permission_string.split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)
