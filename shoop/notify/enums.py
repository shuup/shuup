# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from enumfields.enums import Enum

UNILINGUAL_TEMPLATE_LANGUAGE = "default"


class TemplateUse(Enum):
    NONE = 0
    UNILINGUAL = 1
    MULTILINGUAL = 2


class ConstantUse(Enum):
    VARIABLE_ONLY = 1
    CONSTANT_ONLY = 2
    VARIABLE_OR_CONSTANT = 3


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
