# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django.views.generic
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

from shuup.core.models import Order, Supplier
from shuup.front.views.dashboard import DashboardViewMixin


class OrderViewMixin(object):
    model = Order

    def get_queryset(self):
        qs = super(OrderViewMixin, self).get_queryset()
        return qs.filter(customer=self.request.customer)


class OrderListView(DashboardViewMixin, OrderViewMixin, django.views.generic.ListView):
    template_name = 'shuup/personal_order_history/order_list.jinja'
    context_object_name = 'orders'


class OrderDetailView(DashboardViewMixin, OrderViewMixin, django.views.generic.DetailView):
    template_name = 'shuup/personal_order_history/order_detail.jinja'
    context_object_name = 'order'


class ReorderView(View):

    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(customer=request.customer, pk=kwargs["pk"])
        except Order.DoesNotExist:
            return HttpResponseRedirect(reverse("shuup:show-order", kwargs=kwargs))

        supplier = Supplier.objects.first()
        for line in order.lines.products():
            request.basket.add_product(
                supplier=supplier,
                shop=request.shop,
                product=line.product,
                quantity=line.quantity
            )

        return HttpResponseRedirect(reverse("shuup:basket"))
