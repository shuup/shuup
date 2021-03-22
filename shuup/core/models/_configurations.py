# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from ._base import ShuupModel
from ._shops import Shop


@python_2_unicode_compatible
class ConfigurationItem(ShuupModel):
    shop = models.ForeignKey(
        on_delete=models.CASCADE, to=Shop, related_name="+", null=True, blank=True, verbose_name=_("shop")
    )
    key = models.CharField(verbose_name=_("key"), max_length=100)
    value = JSONField(verbose_name=_("value"))

    class Meta:
        unique_together = [("shop", "key")]
        verbose_name = _("configuration item")
        verbose_name_plural = _("configuration items")

    def __str__(self):
        if self.shop:
            return _("%(key)s for shop %(shop)s") % dict(key=self.key, shop=self.shop)
        else:
            return _("%(key)s (global)") % dict(key=self.key)

    def __repr__(self):
        return '<%s "%s" for %r>' % (type(self).__name__, self.key, self.shop)
