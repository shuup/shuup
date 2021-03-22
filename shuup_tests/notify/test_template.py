# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest

from shuup.notify.script import Context
from shuup.notify.template import NoLanguageMatches
from shuup_tests.notify.fixtures import (
    TEST_TEMPLATE_DATA,
    TEST_TEMPLATE_LANGUAGES,
    TEST_UNI_TEMPLATE_DATA,
    ATestTemplateUsingAction,
    ATestUnilingualTemplateUsingAction,
    get_test_template,
)


def test_template_render(template=None):
    template = get_test_template()
    # since both subject and body are required, "sw" is disqualified
    fields = {
        "subject": None,
        "body": None,
    }
    japanese_render = template.render_first_match(TEST_TEMPLATE_LANGUAGES, fields)
    assert japanese_render["_language"] == "ja"
    # test that |upper worked
    assert template.context.get("name").upper() in japanese_render["body"]


def test_some_fields_language_fallback():
    template = get_test_template()
    fields = {"body": None}
    assert template.render_first_match(TEST_TEMPLATE_LANGUAGES, fields)["_language"] == "sw"


def test_no_language_matches():
    template = get_test_template()
    fields = {
        "body": None,
    }
    with pytest.raises(NoLanguageMatches):
        template.render_first_match(("xx",), fields)


def test_template_in_action():
    ac = ATestTemplateUsingAction(data={"template_data": TEST_TEMPLATE_DATA})
    context = Context.from_variables(name="Sir Test")
    template = ac.get_template(context)
    test_template_render(template)
    japanese_render = ac.get_template_values(context, ("ja",))
    name = template.context.get("name")
    assert name.upper() in japanese_render["body"]
    ac = ATestUnilingualTemplateUsingAction(data={"template_data": TEST_UNI_TEMPLATE_DATA})
    assert name in ac.get_template_values(context)["subject"]
