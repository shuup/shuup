# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from shuup.utils.importing import cached_load

CUBIC_MM_TO_CUBIC_METERS_DIVISOR = Decimal("1000000000")
GRAMS_TO_KILOGRAMS_DIVISOR = 1000


class DefaultMeasurementProvider:
    """
    Default implementation for calculating widths and volumes in various places.

    Can be overridden with the setting SHUUP_MEASUREMENT_PROVIDER_SPEC.

    This implementation relies on these settings having their respective default values:
      - SHUUP_UNIT_PRODUCT_LENGTH = "mm"
      - SHUUP_UNIT_PRODUCT_WEIGHT = "g"
      - SHUUP_UNIT_SHIPMENT_VOLUME = "m3"
      - SHUUP_UNIT_SHIPMENT_WEIGHT = "kg"
      - SHUUP_UNIT_SHIPMENT_PRODUCT_VOLUME = "m3"
      - SHUUP_UNIT_SHIPMENT_PRODUCT_WEIGHT = "g"
    """
    SHIPMENT_PRODUCT_VOLUME_DIVISOR = CUBIC_MM_TO_CUBIC_METERS_DIVISOR
    SHIPMENT_WEIGHT_DIVISOR = GRAMS_TO_KILOGRAMS_DIVISOR

    @classmethod
    def get_shipment_volume(cls, shipment):
        """
        Return the volume of a Shipment.

        :type shipment: shuup.core.models.Shipment
        :rtype: decimal.Decimal
        """
        total_volume = 0
        for quantity, volume in shipment.products.values_list("quantity", "unit_volume"):
            total_volume += quantity * volume
        return total_volume

    @classmethod
    def get_shipment_weight(cls, shipment):
        """
        Return the weight of a Shipment.

        :type shipment: shuup.core.models.Shipment
        :rtype: decimal.Decimal
        """
        total_weight = 0
        for quantity, weight in shipment.products.values_list("quantity", "unit_weight"):
            total_weight += quantity * weight
        return total_weight / cls.SHIPMENT_WEIGHT_DIVISOR

    @classmethod
    def get_shipment_product_volume(cls, shipment_product):
        """
        Return the volume of a ShipmentProduct.

        :type shipment_product: shuup.core.models.ShipmentProduct
        :rtype: decimal.Decimal
        """
        prod = shipment_product.product
        return (prod.width * prod.height * prod.depth) / cls.SHIPMENT_PRODUCT_VOLUME_DIVISOR

    @classmethod
    def get_shipment_product_weight(cls, shipment_product):
        """
        Return the weight of a ShipmentProduct.

        :type shipment_product: shuup.core.models.ShipmentProduct
        :rtype: decimal.Decimal
        """
        return shipment_product.product.gross_weight


def get_measurement_provider():
    return cached_load("SHUUP_MEASUREMENT_PROVIDER_SPEC")


def get_shipment_volume(products):
    return get_measurement_provider().get_shipment_volume(products)


def get_shipment_weight(products):
    return get_measurement_provider().get_shipment_weight(products)


def get_shipment_product_volume(shipment_product):
    return get_measurement_provider().get_shipment_product_volume(shipment_product)


def get_shipment_product_weight(shipment_product):
    return get_measurement_provider().get_shipment_product_weight(shipment_product)
