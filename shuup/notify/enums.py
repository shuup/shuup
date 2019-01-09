# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from enumfields.enums import Enum

UNILINGUAL_TEMPLATE_LANGUAGE = "default"


class TemplateUse(Enum):
    NONE = 0
    UNILINGUAL = 1
    MULTILINGUAL = 2

    class Labels:
        NONE = _('none')
        UNILINGUAL = _('unilingual')
        MULTILINGUAL = _('multilingual')


class ConstantUse(Enum):
    VARIABLE_ONLY = 1
    CONSTANT_ONLY = 2
    VARIABLE_OR_CONSTANT = 3

    class Labels:
        VARIABLE_ONLY = _('variable only')
        CONSTANT_ONLY = _('constant only')
        VARIABLE_OR_CONSTANT = _('variable or constant')


class StepNext(Enum):
    CONTINUE = "continue"
    STOP = "stop"

    class Labels:
        CONTINUE = _("continue to the next step")
        STOP = _("stop processing")


class StepConditionOperator(Enum):
    ALL = "all"
    ANY = "any"
    NONE = "none"

    class Labels:
        ALL = _("all")
        ANY = _("any")
        NONE = _("none")


class RecipientType(Enum):
    ADMINS = 1
    SPECIFIC_USER = 2

    class Labels:
        ADMINS = _("any shop administrator")
        SPECIFIC_USER = _("a specific user")


class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

    class Labels:
        LOW = _('low')
        NORMAL = _('normal')
        HIGH = _('high')
        CRITICAL = _('critical')
