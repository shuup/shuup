# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url('^saved-carts/$', views.CartListView.as_view(),
        name='saved_cart.list'),
    url('^saved-carts/save/$', views.CartSaveView.as_view(),
        name='saved_cart.save'),
    url('^saved-carts/(?P<pk>\d+)/add/$', views.CartAddAllProductsView.as_view(),
        name='saved_cart.add_all'),
    url('^saved-carts/(?P<pk>\d+)/delete/$', views.CartDeleteView.as_view(),
        name='saved_cart.delete'),
    url('^saved-carts/(?P<pk>.+)/$', views.CartDetailView.as_view(),
        name='saved_cart.detail')
)
