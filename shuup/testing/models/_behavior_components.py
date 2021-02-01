# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ValidationError

from shuup.core.models import ServiceBehaviorComponent, ServiceCost


class ExpensiveSwedenBehaviorComponent(ServiceBehaviorComponent):
    name = "Expenseefe-a Svedee Sheepping"

    def get_costs(self, service, source):
        four = source.create_price('4.00')
        five = source.create_price('5.00')
        if source.shipping_address and source.shipping_address.country == "SE":
            yield ServiceCost(five, base_price=four)
        else:
            yield ServiceCost(four)

    def get_unavailability_reasons(self, service, source):
        if source.shipping_address and source.shipping_address.country == "FI":
            yield ValidationError("Probleema!! Veell nut sheep unytheeng tu Feenlund!", code="we_no_speak_finnish")
