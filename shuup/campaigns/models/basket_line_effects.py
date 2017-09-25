# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import PolymorphicShuupModel


class BasketLineEffect(PolymorphicShuupModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey("BasketCampaign", related_name='line_effects', verbose_name=_("campaign"))

    def get_discount_lines(self, order_source, original_lines):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Iterable[shuup.core.order_creator.SourceLine]
        """
        raise NotImplementedError("Not implemented!")
