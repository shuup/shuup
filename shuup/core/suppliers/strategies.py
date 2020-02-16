# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class FirstSupplierStrategy(object):

    def get_supplier(self, **kwargs):
        return kwargs["shop_product"].suppliers.enabled().first()
