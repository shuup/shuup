# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import six

from shuup.apps.provides import get_provide_specs_and_objects
from shuup.utils.importing import load
from shuup.utils.text import force_ascii


class ModuleNotFound(ValueError):
    pass


class ModuleInterface(object):
    _cached_modules_impl = None
    module_options_field = "module_data"  # May be overridden on class level
    module_provides_key = None

    def _load_modules(self):
        enabled_supplier_modules = self.supplier_modules.all()
        loaded_modules = []
        options = getattr(self, self.module_options_field, None) or {}

        for supplier_module in enabled_supplier_modules:
            impls = self.get_module_implementation_map()
            if supplier_module.module_identifier not in impls:
                raise ModuleNotFound(
                    "Invalid module identifier %r in %s" % (supplier_module.name, force_ascii(repr(self)))
                )
            spec = impls[supplier_module.module_identifier]
            module = load(spec, context_explanation="Loading module for %s" % force_ascii(repr(self)))
            loaded_modules.append(module(self, options))

        return loaded_modules

    @property
    def modules(self):
        if not getattr(self, "_cached_modules_impl", None):
            self._cached_modules_impl = self._load_modules()
        return self._cached_modules_impl

    @classmethod
    def get_module_implementation_map(cls):
        """
        Get a dict that maps module spec identifiers (short strings) into actual spec names.

        As an example::

            {"Eggs": "foo_package.bar_module:EggsClass"}

        :rtype: dict[str, str]
        """
        identifier_to_spec = {}
        for spec, module in six.iteritems(get_provide_specs_and_objects(cls.module_provides_key)):
            if module.identifier:
                identifier_to_spec[module.identifier] = spec
        return identifier_to_spec
