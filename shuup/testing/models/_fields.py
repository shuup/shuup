# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models

from shuup.core.fields import SeparatedValuesField


class FieldsModel(models.Model):
    separated_values = SeparatedValuesField(blank=True)
    separated_values_semi = SeparatedValuesField(blank=True, separator=";")
    separated_values_dash = SeparatedValuesField(blank=True, separator="-")
