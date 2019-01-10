# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Product
from shuup.core.utils.model_caching_descriptor import ModelCachingDescriptor


class ProductCachingObject(object):
    _descriptor = ModelCachingDescriptor("product", queryset=Product.objects.all())
    product = _descriptor.object_property
    product_id = _descriptor.id_property
