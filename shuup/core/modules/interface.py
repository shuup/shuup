# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import six
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import (
    get_provide_objects, get_provide_specs_and_objects
)
from shuup.utils.importing import load
from shuup.utils.text import force_ascii


class ModuleNotFound(ValueError):
    pass


class ModuleInterface(object):
    _cached_module_impl = None
    default_module_spec = None  # Overridden on class level
    module_identifier = None  # Overridden on class level
    module_options_field = "module_data"  # May be overridden on class level
    module_provides_key = None

    def _load_module(self):
        spec = self.default_module_spec
        module_identifier = self.module_identifier
        if module_identifier:
            impls = self.get_module_implementation_map()
            if module_identifier not in impls:
                raise ModuleNotFound(
                    "Invalid module identifier %r in %s" % (module_identifier, force_ascii(repr(self)))
                )
            spec = impls[module_identifier]

        cls = load(spec, context_explanation="Loading module for %s" % force_ascii(repr(self)))

        options = getattr(self, self.module_options_field, None) or {}
        return cls(self, options)

    @property
    def module(self):
        if not getattr(self, "_cached_module_impl", None):
            self._cached_module_impl = self._load_module()
        return self._cached_module_impl

    @classmethod
    def get_module_choices(cls, empty_label=None):
        if empty_label is None:
            empty_label = _('No Choice')
        choices = [("", empty_label)]

        for module in get_provide_objects(cls.module_provides_key):
            if module.identifier:
                choices.append((
                    module.identifier,
                    getattr(module, "name", None) or module.identifier
                ))
        choices.sort()
        return choices

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
