# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.conf.urls import include, patterns, url
from django.conf.urls.static import static
from django.contrib import admin

from shuup.front.views.checkout import SinglePageCheckoutView


class SinglePageCheckoutViewWithLoginAndRegister(SinglePageCheckoutView):
    phase_specs = [
        "shuup.front.checkout.checkout_method:CheckoutMethodPhase",
        "shuup.front.checkout.checkout_method:RegisterPhase",
        "shuup.front.checkout.addresses:AddressesPhase",
        "shuup.front.checkout.methods:MethodsPhase",
        "shuup.front.checkout.methods:ShippingMethodPhase",
        "shuup.front.checkout.methods:PaymentMethodPhase",
        "shuup.front.checkout.confirm:ConfirmPhase",
    ]
    empty_phase_spec = "shuup.front.checkout.empty:EmptyPhase"


urlpatterns = patterns(
    '',
    url(r'^checkout/$', SinglePageCheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
    url(r'^checkout/(?P<phase>.+)/$', SinglePageCheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^sa/', include('shuup.admin.urls', namespace="shuup_admin", app_name="shuup_admin")),
    url(r'^api/', include('shuup.api.urls')),
    url(r'^', include('shuup.front.urls', namespace="shuup", app_name="shuup")),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
