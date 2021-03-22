# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms

from shuup.notify.base import Action, Event, Variable
from shuup.notify.enums import UNILINGUAL_TEMPLATE_LANGUAGE, StepConditionOperator, TemplateUse
from shuup.notify.models import Script
from shuup.notify.script import Context
from shuup.notify.template import Template
from shuup.notify.typology import Language, Model, Text
from shuup.testing.factories import create_random_order, create_random_person, get_default_product
from shuup.testing.text_data import random_title

TEST_STEP_DATA = [
    {
        "next": "continue",
        "actions": [{"identifier": "set_debug_flag", "flag_name": {"constant": "success"}}],
        "conditions": [
            {"identifier": "language_equal", "v1": {"variable": "order_language"}, "v2": {"constant": "fi"}},
            {"identifier": "language_equal", "v1": {"variable": "order_language"}, "v2": {"constant": "ja"}},
        ],
        "cond_op": StepConditionOperator.ANY.value,
        "enabled": True,
    },
]

TEST_TEMPLATE_DATA = {
    "en": {
        # English
        "subject": "Hello, {{ name }}!",
        "body": "Hi, {{ name }}. This is a test.",
        "content_type": "plain",
    },
    "ja": {
        # Japanese
        "subject": "こんにちは、{{ name|upper }}！",
        "body": "こんにちは、{{ name|upper }}.これはテストです。",
        "content_type": "html",
    },
    "sw": {
        # Swahili
        "body": "Hi, {{ name }}. Hii ni mtihani.",
        "content_type": "plain",
    },
}

TEST_UNI_TEMPLATE_DATA = {
    UNILINGUAL_TEMPLATE_LANGUAGE: {
        "subject": "This is a kokeilu {{ name }}",
        "body": "tämä on a test",
        "content_type": "plain",
    }
}

TEST_TEMPLATE_LANGUAGES = ("sw", "ja", "en")


class ATestEvent(Event):
    identifier = "test_event"
    log_target_variable = "order"

    order_language = Variable(name="Order Language", type=Language)
    just_some_text = Variable(name="Just Some Text", type=Text)
    order = Variable(name="Order", type=Model("shuup.Order"))


class ATestTemplateUsingAction(Action):
    identifier = "test_template_action"
    template_use = TemplateUse.MULTILINGUAL
    template_fields = {"subject": forms.CharField(), "body": forms.CharField(), "content_type": forms.CharField()}


class ATestUnilingualTemplateUsingAction(Action):
    identifier = "test_unilingual_template_action"
    template_use = TemplateUse.UNILINGUAL
    template_fields = {"subject": forms.CharField(), "body": forms.CharField(), "content_type": forms.CharField()}


def get_test_script():
    sc = Script()
    sc.set_serialized_steps(TEST_STEP_DATA)
    return sc


def get_initialized_test_event(identifier=None):
    get_default_product()
    customer = create_random_person()
    order = create_random_order(customer)
    return ATestEvent(order_language=order.language, order=order, just_some_text=random_title())


def get_test_template():
    ctx = Context.from_variables(name="Sir Test")
    template = Template(ctx, TEST_TEMPLATE_DATA)
    return template
