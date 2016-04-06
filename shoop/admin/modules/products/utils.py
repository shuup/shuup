# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.models import ProductPackageLink


def clear_existing_package(parent_product):
    """
    Utility function for clearing existing package.
    """
    children = parent_product.get_package_child_to_quantity_map().keys()
    ProductPackageLink.objects.filter(parent=parent_product).delete()
    parent_product.verify_mode()
    parent_product.save()
    for child in children:
        child.verify_mode()
        child.save()
