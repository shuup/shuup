# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import warnings

import six
from django.contrib.auth.models import Permission

from shuup import configuration


def get_default_model_permissions(model):
    """
    Return a set of all default permissions for a given model.

    :param model: Model class
    :type model: django.db.Model
    :return: Set of default model permissions as strings
    :rtype: set[str]
    """
    warnings.warn(
        "get_default_model_permissions is deprecated in Shuup 2.0. Use human readable permission strings instead.",
        DeprecationWarning
    )
    permissions = set()

    for default in model._meta.default_permissions:
        permissions.add("%s.%s_%s" % (model._meta.app_label, default, model._meta.model_name))

    return permissions


def get_missing_permissions(user, permissions):
    """
    Return a set of missing permissions for a given iterable of
    permission strings.

    1. Check missing permissions using `User.has_perm`-method
       allows us to use Django model permissions.
    2. Check missing permissions using Shuup admin custom
       permissions which are stored to configuration items
       per user group.

    :param user: User instance to check for permissions
    :type user: django.contrib.auth.models.User
    :param permissions: Iterable of permission strings
    :type permissions: Iterable[str]
    :return: Set of missing permission strings
    :rtype: set[str]
    """
    if getattr(user, "is_superuser", False):
        return set()

    group_permissions = get_permissions_from_groups(user.groups.values_list("pk", flat=True))
    if group_permissions:
        missing_permissions = set(p for p in set(permissions) if p not in group_permissions)
    else:
        missing_permissions = set(permissions)

    return missing_permissions


def has_permission(user, permission):
    """
    Returns whether user has permission for a given permission string.

    :param user: User instance to check for permission
    :type user: django.contrib.auth.models.User
    :param permission: Permission string
    :type permission: str
    :return: Whether user has permission
    :rtype: bool
    """
    return not bool(get_missing_permissions(user, [permission]))


def _get_permission_key_for_group(group_id):
    return "%s_admin_permissions" % group_id


def get_permissions_for_user(user):
    return get_permissions_from_groups(user.groups.values_list("pk", flat=True))


def get_permissions_from_group(group):
    group_id = (group if isinstance(group, six.integer_types) else group.pk)
    return set(configuration.get(None, _get_permission_key_for_group(group_id), default=[]))


def set_permissions_for_group(group, permissions):
    group_id = (group if isinstance(group, six.integer_types) else group.pk)
    configuration.set(None, _get_permission_key_for_group(group_id), permissions)


def get_permissions_from_groups(groups):
    permissions = set()
    for group in groups:
        group_id = (group if isinstance(group, six.integer_types) else group.pk)
        permissions |= get_permissions_from_group(group_id)
    return permissions


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
    warnings.warn(
        "get_permission_object_from_string is deprecated in Shuup 2.0. Django permission shouldn't be needed.",
        DeprecationWarning
    )
    app_label, codename = permission_string.split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def get_permissions_for_module_url(admin_module, url_name):
    """
    Returns a set of permissions for a given admin module that match with `url_name`.

    If the url_name doesn't match with any admin url, a blank set is returned

    :param admin_module: The admin module to return permissions
    :type admin_module: shuup.admin.AdminModule
    :param url_name: the url name
    :type url_name: string
    :return: Set of permissions for the given module and url
    :rtype: set[str]
    """
    for url in admin_module.get_urls():
        if url.name == url_name:
            return get_permissions_from_urls([url])
    return set()
