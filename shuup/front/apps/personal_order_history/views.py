# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import django.views.generic

import shuup.core.models


class OrderViewMixin(object):
    model = shuup.core.models.Order

    def get_queryset(self):
        qs = super(OrderViewMixin, self).get_queryset()
        return qs.filter(customer=self.request.customer)


class OrderListView(OrderViewMixin, django.views.generic.ListView):
    template_name = 'shuup/personal_order_history/order_list.jinja'
    context_object_name = 'orders'


class OrderDetailView(OrderViewMixin, django.views.generic.DetailView):
    template_name = 'shuup/personal_order_history/order_detail.jinja'
    context_object_name = 'order'
