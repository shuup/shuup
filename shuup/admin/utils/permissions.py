# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from shuup.core.models import ShopObjectPermission


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
        permissions.add(get_permission_string_for_model(model, default))

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
        missing_permissions = set(p for p in set(permissions) if p is not None and not user.has_perm(p))
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


def user_has_permission(perm, user, obj):
    if getattr(user, "is_superuser", False):
        return True

    permission_str = get_permission_string_for_object(obj, perm)
    if not permission_str:
        return False

    check_per_object_permission = settings.SHUUP_CHECK_PER_OBJECT_PERMISSIONS and obj.pk
    return user.has_perm(permission_str, obj=(obj if check_per_object_permission else None))


def get_permission_string_for_model(model, perm):
    if not model:
        return
    model_permission = validate_and_get_permission(model, perm)
    if not model_permission:
        return

    # We sometimes end up with a permission like `view_shopproduct_shopproduct`
    # This is primarily due to how permission names are defined in the models
    # We are likely sending the wrong `perm` parameter value.
    permission = "%s.%s" % (model._meta.app_label, model_permission)
    if not permission.endswith(model._meta.model_name):
        permission += "_%s" % model._meta.model_name
    return permission


def validate_and_get_permission(model, perm):
    for default in model._meta.default_permissions:
        if default == perm:
            return default
    for permission_code, permission_str in model._meta.permissions:
        if permission_code.startswith(perm):
            return permission_code


def get_permission_string_for_object(obj, perm):
    model = type(obj)
    return get_permission_string_for_model(model, perm) if hasattr(model, "_meta") else None


def filter_queryset(request, perm, queryset):
    if getattr(request.user, "is_superuser", False) or not settings.SHUUP_CHECK_PER_OBJECT_PERMISSIONS:
        return queryset

    app_label, codename = perm.split(".", 1)
    ctype = ContentType.objects.filter(app_label=app_label, permission__codename=codename).first()

    object_ids = set(
        ShopObjectPermission.objects.filter(
            shop=request.session.get("admin_shop"), content_type=ctype
        ).values_list("object_id", flat=True))

    return queryset.filter(Q(pk__in=object_ids))
