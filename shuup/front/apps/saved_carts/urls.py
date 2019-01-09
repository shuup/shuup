# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url('^saved-carts/$', login_required(views.CartListView.as_view()),
        name='saved_cart.list'),
    url('^saved-carts/save/$', login_required(views.CartSaveView.as_view()),
        name='saved_cart.save'),
    url('^saved-carts/(?P<pk>\d+)/add/$', login_required(views.CartAddAllProductsView.as_view()),
        name='saved_cart.add_all'),
    url('^saved-carts/(?P<pk>\d+)/delete/$', login_required(views.CartDeleteView.as_view()),
        name='saved_cart.delete'),
    url('^saved-carts/(?P<pk>.+)/$', login_required(views.CartDetailView.as_view()),
        name='saved_cart.detail')
]
