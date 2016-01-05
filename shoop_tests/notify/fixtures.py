# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms

from shoop.notify import Context
from shoop.notify.base import Action, Event, Variable
from shoop.notify.enums import (
    StepConditionOperator, TemplateUse, UNILINGUAL_TEMPLATE_LANGUAGE
)
from shoop.notify.models import Script
from shoop.notify.template import Template
from shoop.notify.typology import Language, Model, Text
from shoop.testing.factories import (
    create_random_order, create_random_person, get_default_product
)
from shoop.testing.text_data import random_title

TEST_STEP_DATA = [
    {
        'next': 'continue',
        'actions': [
            {
                'identifier': 'set_debug_flag',
                'flag_name': {'constant': 'success'}
            }
        ],
        'conditions': [
            {
                'identifier': 'language_equal',
                'v1': {'variable': 'order_language'},
                'v2': {'constant': 'fi'}
            },
            {
                'identifier': 'language_equal',
                'v1': {'variable': 'order_language'},
                'v2': {'constant': 'ja'}
            },
        ],
        'cond_op': StepConditionOperator.ANY.value,
        'enabled': True
    },
]

TEST_TEMPLATE_DATA = {
    "en": {
        # English
        "subject": "Hello, {{ name }}!",
        "body": "Hi, {{ name }}. This is a test."
    },
    "ja": {
        # Japanese
        "subject": u"こんにちは、{{ name|upper }}！",
        "body": u"こんにちは、{{ name|upper }}.これはテストです。"
    },
    "sw": {
        # Swahili
        "body": "Hi, {{ name }}. Hii ni mtihani."
    }
}

TEST_UNI_TEMPLATE_DATA = {
    UNILINGUAL_TEMPLATE_LANGUAGE: {
        "subject": u"This is a kokeilu {{ name }}",
        "body": u"tämä on a test"
    }
}

TEST_TEMPLATE_LANGUAGES = ("sw", "ja", "en")


class TestEvent(Event):
    identifier = "test_event"
    log_target_variable = "order"

    order_language = Variable(name="Order Language", type=Language)
    just_some_text = Variable(name="Just Some Text", type=Text)
    order = Variable(name="Order", type=Model("shoop.Order"))


class TestTemplateUsingAction(Action):
    identifier = "test_template_action"
    template_use = TemplateUse.MULTILINGUAL
    template_fields = {
        "subject": forms.CharField(),
        "body": forms.CharField()
    }


class TestUnilingualTemplateUsingAction(Action):
    identifier = "test_unilingual_template_action"
    template_use = TemplateUse.UNILINGUAL
    template_fields = {
        "subject": forms.CharField(),
        "body": forms.CharField()
    }


def get_test_script():
    sc = Script()
    sc.set_serialized_steps(TEST_STEP_DATA)
    return sc


def get_initialized_test_event():
    get_default_product()
    customer = create_random_person()
    order = create_random_order(customer)
    return TestEvent(
        order_language=order.language,
        order=order,
        just_some_text=random_title()
    )


def get_test_template():
    ctx = Context.from_variables(name=u"Sir Test")
    template = Template(ctx, TEST_TEMPLATE_DATA)
    return template
