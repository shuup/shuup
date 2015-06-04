# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.models import Product
from shoop.core.utils.model_caching_descriptor import ModelCachingDescriptor


class ProductCachingObject(object):
    _descriptor = ModelCachingDescriptor("product", queryset=Product.objects.all())
    product = _descriptor.object_property
    product_id = _descriptor.id_property
