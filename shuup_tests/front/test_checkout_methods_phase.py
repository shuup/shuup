# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.utils.translation import activate

from shuup.front.views.checkout import BaseCheckoutView
from shuup.testing.utils import apply_request_middleware


class CheckoutMethodsOnlyCheckoutView(BaseCheckoutView):
    phase_specs = ["shuup.front.checkout.checkout_method:CheckoutMethodPhase"]


@pytest.mark.django_db
def test_checkout_method_phase_basic(rf):
    activate("en")
    view = CheckoutMethodsOnlyCheckoutView.as_view()

    request = apply_request_middleware(rf.get("/"))
    response = view(request=request, phase="checkout_method")
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200
