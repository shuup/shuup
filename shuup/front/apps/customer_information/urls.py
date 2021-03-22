# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r"^address-book/$", login_required(views.AddressBookView.as_view()), name="address_book"),
    url(
        r"^address-book/edit/(?P<pk>\d+)$",
        login_required(views.AddressBookEditView.as_view()),
        name="address_book_edit",
    ),
    url(r"^address-book/edit/new$", login_required(views.AddressBookEditView.as_view()), name="address_book_new"),
    url(r"^address-book/delete/(?P<pk>\d+)$", login_required(views.delete_address), name="address_book_delete"),
    url(r"^customer/$", login_required(views.CustomerEditView.as_view()), name="customer_edit"),
    url(
        r"^customer/change-password/$", login_required(views.CustomPasswordChangeView.as_view()), name="change_password"
    ),
    url(r"^company/$", login_required(views.CompanyEditView.as_view()), name="company_edit"),
]
