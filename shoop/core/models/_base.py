# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import parler.models
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from shoop.utils import text


class ShoopModel(models.Model):
    """
    Shoop Model.
    """
    identifier_attr = 'identifier'

    def __repr__(self):
        if hasattr(self, self.identifier_attr):
            identifier = getattr(self, self.identifier_attr) or ''
            identifier_suf = '-{}'.format(text.force_ascii(identifier))
        else:
            identifier_suf = ''
        return '<{}:{}{}>'.format(type(self).__name__, self.pk, identifier_suf)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class TranslatableShoopModel(ShoopModel, parler.models.TranslatableModel):
    name_attr = 'name'

    def __str__(self):
        name = self.safe_translation_getter(self.name_attr, any_language=True)
        if name is None:
            return '{}:{}'.format(type(self).__name__, self.pk)
        return name

    class Meta:
        abstract = True
