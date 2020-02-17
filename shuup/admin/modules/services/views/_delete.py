# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.urlresolvers import reverse_lazy
from django.views.generic import DeleteView

from shuup.core.models import PaymentMethod, ShippingMethod


class PaymentMethodDeleteView(DeleteView):
    model = PaymentMethod
    success_url = reverse_lazy("shuup_admin:payment_method.list")


class ShippingMethodDeleteView(DeleteView):
    model = ShippingMethod
    success_url = reverse_lazy("shuup_admin:shipping_method.list")
