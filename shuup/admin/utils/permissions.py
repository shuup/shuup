# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from logging import getLogger

from django.contrib.auth.models import ContentType, Permission
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.core import cache

LOGGER = getLogger(__name__)


#class PermissionDef(object):
#    model = None
#    codename = None
#    permission_key = None
#    name = None
#
#    def __init__(self, model, codename, name=None):
#        self.model = model
#        self.codename = codename
#        self.permission_key = "%s.%s" % (model._meta.app_label, self.codename)
#        self.name = name
#
#    def ensure(self):
#        """
#        Create the permission in database if needed
#        """
#        cache_key = "perm:%s" % self.permission_key
#        cached_value = cache.get(cache_key)
#        if cached_value is not None:
#            return
#        content_type = ContentType.objects.get_for_model(self.model)
#        permission = Permission.objects.update_or_create(
#            codename=self.codename,
#            content_type=content_type,
#            defaults=dict(name=force_text(self.name))
#        )[0]
#        cache.set(cache_key, permission)
#
#    def __str__(self):
#        return self.permission_key
#
#    def __repr__(self):
#        return self.__str__()
#
#
#class AdminDefaultModelPermissionDef(PermissionDef):
#    operation = None
#
#    def __init__(self, model, operation):
#        """
#        Create a permission definition from a model and operation
#
#        :param model: Model class
#        :type model: django.db.Model
#        :param operation: the operation (add, change, delete, etc.)
#        :type operation: string
#        """
#        # use the base permission name, eg: "Can delete shops"
#        self.operation = operation
#
#        codename = "%s_%s" % (operation, model._meta.model_name)
#        name = _("Can {operation} {model_verbose_name}").format(
#            operation=operation,
#            model_verbose_name=model._meta.verbose_name_plural
#        )
#        super(AdminDefaultModelPermissionDef, self).__init__(model, codename, name)
#
#
#class AdminCustomModelPermissionDef(PermissionDef):
#    def __init__(self, model, codename, name):
#        """
#        Create a permission definition from a model and custom codename and name
#
#        :param model: Model class
#        :type model: django.db.Model
#        :param codename: the permission codename name
#        :type codename: string
#        :param name: the name of the custom permission
#        :type name: string
#        """
#        assert "." not in codename, "Dot notation is not allowed in codename"
#        # to prevent duplicate codenames, we add the model name as a prefix to the codename
#        codename = "%s_%s" % (model._meta.model_name, codename)
#        super(AdminCustomModelPermissionDef, self).__init__(model, codename, name)
#
#    def ensure(self):
#        cache_key = "perm:%s" % self.permission_key
#        cached_value = cache.get(cache_key)
#        if cached_value is not None:
#            return
#        content_type = ContentType.objects.get_for_model(self.model)
#        permission = Permission.objects.update_or_create(
#            codename=self.codename,
#            content_type=content_type,
#            defaults=dict(name=self.name)
#        )[0]
#        cache.set(cache_key, permission)
#
#
#class AdminModulePermissionDef(PermissionDef):
#    def __init__(self, admin_module):
#        """
#        Create a permission definition from an admin module
#
#        :param admin_module: admin module
#        :type model: shuup.admin.AdminModule
#        """
#        from shuup.core.models import Shop
#        name = _("Access {module_name}").format(module_name=admin_module.name)
#        codename = "admin_module:{}:{}".format(
#            admin_module.__class__.__module__.replace(".", "-"),
#            admin_module.__class__.__name__
#        )
#        super(AdminModulePermissionDef, self).__init__(Shop, codename, name)


def get_permission_str(model, permission):
    """
    Return permission string for given model and permission
    combination. Caller is responsible that the permission
    actually exists for the model

    :param model: Model class
    :param permission: Permission string eg. change, delete, add or viw
    :return: permission string
    :rtype: str
    """
    return "%s.%s_%s" % (model._meta.app_label, permission, model._meta.model_name)


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
    permissions = set(str(p) for p in permissions)

    if callable(getattr(user, 'has_perm', None)):
        missing_permissions = set(p for p in permissions if not user.has_perm(p))
    else:
        missing_permissions = permissions

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

    :param permission_string: Permission string or a permission definition instance
    :type permission_strings: str|BasePermissionDef
    :return: Permission object
    :rtype: django.contrib.auth.models.Permission
    """
    app_label, codename = str(permission_string).split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def ensure_admin_permissions():
    from shuup.admin.module_registry import get_modules

    # go through all permissions of the admin module and create them if needed
    LOGGER.debug("Ensuring admin module permissions...")

    for admin_module in get_modules():
        for permission in admin_module.get_required_permissions():
            if issubclass(permission.__class__, PermissionDef):
                permission.ensure()

        for module_url in admin_module.get_urls():
            for permission in module_url._permissions:
                if issubclass(permission.__class__, PermissionDef):
                    permission.ensure()

    LOGGER.debug("Done.")
