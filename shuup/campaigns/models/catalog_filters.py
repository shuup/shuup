# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel


class CatalogFilter(PolymorphicModel):
    model = None

    identifier = "base_catalog_filter"
    name = _("Base Catalog Filter")

    active = models.BooleanField(default=True, verbose_name=_("active"))

    def filter_queryset(self, queryset):
        raise NotImplementedError("Subclasses should implement `filter_queryset`")
