# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest

from shoop.notify import Context
from shoop.notify.template import NoLanguageMatches
from shoop_tests.notify.fixtures import (
    ATestTemplateUsingAction, ATestUnilingualTemplateUsingAction,
    get_test_template, TEST_TEMPLATE_DATA, TEST_TEMPLATE_LANGUAGES,
    TEST_UNI_TEMPLATE_DATA
)


def test_template_render(template=None):
    template = get_test_template()
    # since both subject and body are required, "sw" is disqualified
    japanese_render = template.render_first_match(TEST_TEMPLATE_LANGUAGES, ("subject", "body"))
    assert japanese_render["_language"] == "ja"
    # test that |upper worked
    assert template.context.get("name").upper() in japanese_render["body"]


def test_some_fields_language_fallback():
    template = get_test_template()
    assert template.render_first_match(TEST_TEMPLATE_LANGUAGES, ("body",))["_language"] == "sw"


def test_no_language_matches():
    template = get_test_template()
    with pytest.raises(NoLanguageMatches):
        template.render_first_match(("xx",), ("body",))


def test_template_in_action():
    ac = ATestTemplateUsingAction(data={"template_data": TEST_TEMPLATE_DATA})
    context = Context.from_variables(name=u"Sir Test")
    template = ac.get_template(context)
    test_template_render(template)
    japanese_render = ac.get_template_values(context, ("ja",))
    name = template.context.get("name")
    assert name.upper() in japanese_render["body"]
    ac = ATestUnilingualTemplateUsingAction(data={"template_data": TEST_UNI_TEMPLATE_DATA})
    assert name in ac.get_template_values(context)["subject"]
