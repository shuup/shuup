# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.utils.multilanguage_model_form import MultiLanguageModelForm

from .models import PaymentWithCheckoutPhase, PseudoPaymentProcessor


class PseudoPaymentProcessorForm(MultiLanguageModelForm):
    class Meta:
        model = PseudoPaymentProcessor
        exclude = ["identifier"]


class PaymentWithCheckoutPhaseForm(MultiLanguageModelForm):
    class Meta:
        model = PaymentWithCheckoutPhase
        exclude = ["identifier"]
