# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.admin.forms import ShuupAdminForm

from .models import (
    CarrierWithCheckoutPhase, PaymentWithCheckoutPhase, PseudoPaymentProcessor
)


class PseudoPaymentProcessorForm(ShuupAdminForm):
    class Meta:
        model = PseudoPaymentProcessor
        exclude = ["identifier"]


class PaymentWithCheckoutPhaseForm(ShuupAdminForm):
    class Meta:
        model = PaymentWithCheckoutPhase
        exclude = ["identifier"]


class CarrierWithCheckoutPhaseForm(ShuupAdminForm):
    class Meta:
        model = CarrierWithCheckoutPhase
        exclude = ["identifier"]
