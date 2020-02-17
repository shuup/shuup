# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Supplier


class UsernameSupplierProvider(object):
    @classmethod
    def get_supplier(cls, request, **kwargs):
        return Supplier.objects.filter(identifier=request.user.username).first()


class RequestSupplierProvider(object):
    @classmethod
    def get_supplier(cls, request, **kwargs):
        return getattr(request, "supplier", None)


class FirstSupplierProvider(object):
    @classmethod
    def get_supplier(cls, request, **kwargs):
        return Supplier.objects.first()
