# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import ProductMode
from shuup.front.forms.order_forms import ProductOrderForm


class DifferentProductOrderForm(ProductOrderForm):
    template_name = "shuup_testing/different_order_form.jinja"

    def is_compatible(self):
        return (self.product.mode == ProductMode.SUBSCRIPTION)
