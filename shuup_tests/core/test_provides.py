# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import uuid

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from shuup.apps.provides import (
    get_identifier_to_object_map, get_identifier_to_spec_map,
    get_provide_objects, get_provide_specs_and_objects, load_module,
    override_provides
)
from shuup_tests.utils import empty_iterable


class IdentifiedObject(object):
    identifier = "identifier"


class UnidentifiedObject(object):
    identifier = None


class VeryUnidentifiedObject(object):
    pass


def test_provides():
    IDENTIFIED_OBJECT_SPEC = "%s:IdentifiedObject" % __name__
    category = str(uuid.uuid4())
    with override_provides(category, [
        IDENTIFIED_OBJECT_SPEC,
        "%s:UnidentifiedObject" % __name__,
        "%s:VeryUnidentifiedObject" % __name__,
    ]):
        objects = get_provide_objects(category)
        assert set(objects) == set((IdentifiedObject, UnidentifiedObject, VeryUnidentifiedObject))
        assert get_identifier_to_object_map(category)["identifier"] == IdentifiedObject
        assert get_identifier_to_spec_map(category)["identifier"] == IDENTIFIED_OBJECT_SPEC
        assert get_provide_specs_and_objects(category)[IDENTIFIED_OBJECT_SPEC] == IdentifiedObject

    # Test the context manager clears things correctly
    assert empty_iterable(get_provide_objects(category))
    assert empty_iterable(get_provide_specs_and_objects(category))
    assert empty_iterable(get_identifier_to_object_map(category))
    assert empty_iterable(get_identifier_to_spec_map(category))


def test_load_module():
    with override_settings(
        INSTALLED_APPS=["shuup_tests.core"],
        MODULE_TEST_MODULE="mtm1"
    ):
        mtm = load_module("MODULE_TEST_MODULE", "module_test_module")
        assert mtm.greeting == "Hello"

    with override_settings(
        INSTALLED_APPS=["shuup_tests.core"],
        MODULE_TEST_MODULE="mtm2"
    ):
        mtm = load_module("MODULE_TEST_MODULE", "module_test_module")
        assert mtm.greeting == "Hola"

    with override_settings(
        MODULE_TEST_MODULE="mtm2"
    ):
        with pytest.raises(ImproperlyConfigured):
            load_module("MODULE_TEST_MODULE", "module_test_module")
