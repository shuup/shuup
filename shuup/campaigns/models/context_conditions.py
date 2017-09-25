# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel


class ContextCondition(PolymorphicModel):
    model = None
    identifier = "context_condition"
    name = _("Context Condition")
    description = _("Context Condition")

    active = models.BooleanField(default=True)

    def matches(self, context):
        return False
