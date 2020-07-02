# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Sum


def get_available_sku(sku=None):
    from shuup.core.models import Product
    """
    Get's the next available sku for a product.

    :param sku: The current sku of a product if prodct already exists.
    :type sku: int, None or str

    :return: The next available sku or the sku passed in
    :rtype: int or str
    """
    if not sku:
        last_id = Product.objects.values_list('id', flat=True).first()
        sku = last_id + 1 if last_id else 1
    return sku


def clone_add_m2m_filed(instance, m2m_objects, field, create_new=False):
    """
    Clones or just adds a m2m field to model instans.

    :param instance: Model class.
    :type instance: django.db.Model
    :param m2m_objects: Queryset of all the m2m objects.
    :type m2m_objects: django.db.models.QuerySet
    :param field: The name of the m2m field.
    :type field: str
    :param create_new: if the m2m instance should be cloned or not.
    :type create_new: boolean

    :return: None
    :rtype: None
    """
    for m2m_object in m2m_objects:
        if create_new:
            m2m_object.pk = None
            if hasattr(m2m_object, "master"):
                m2m_object.master = instance    
            m2m_object.save()
        getattr(instance, field).add(m2m_object)
