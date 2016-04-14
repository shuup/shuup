# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.admin.forms import ShoopAdminForm

from .models import PaymentWithCheckoutPhase, PseudoPaymentProcessor


class PseudoPaymentProcessorForm(ShoopAdminForm):
    class Meta:
        model = PseudoPaymentProcessor
        exclude = ["identifier"]


class PaymentWithCheckoutPhaseForm(ShoopAdminForm):
    class Meta:
        model = PaymentWithCheckoutPhase
        exclude = ["identifier"]
