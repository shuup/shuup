# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import contextlib

import six

from shoop.apps.provides import get_provide_objects
from shoop.utils.importing import load

_registry = []


def register(module_class):
    if isinstance(module_class, six.string_types):
        module_class = load(module_class, "Admin Module")
    _registry.append(module_class())


def discover():
    for obj in get_provide_objects("admin_module"):
        register(obj)


def get_modules():
    """
    :rtype: list[shoop.admin.base.AdminModule]
    """
    if not _registry:
        discover()
    return iter(_registry)


def get_module_urls():
    for module in get_modules():  # pragma: no branch
        for url in module.get_urls():  # pragma: no branch
            yield url


@contextlib.contextmanager
def replace_modules(new_module_classes):
    """
    Context manager to temporarily replace all modules with something else.

    Test utility, mostly.

    >>> def some_test():
    ...     with replace_modules(["foo.bar:QuuxModule"]):
    ...         pass # do stuff

    :param new_module_classes: Iterable of module classes, like you'd pass to `register`
    """
    old_registry = _registry[:]
    _registry[:] = []
    for cls in new_module_classes:
        register(cls)
    try:
        yield
    finally:
        _registry[:] = old_registry
