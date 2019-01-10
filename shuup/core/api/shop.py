# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import babel
import django_filters
from django.db.models.expressions import RawSQL
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import filters, serializers, viewsets
from rest_framework.settings import api_settings

from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.serializers import LabelSerializer
from shuup.core.models import Currency, Shop, ShopStatus
from shuup.utils.i18n import get_current_babel_locale


class CurrencySerializer(serializers.ModelSerializer):
    symbol = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        exclude = ["id"]

    def get_symbol(self, currency):
        return babel.numbers.get_currency_symbol(currency.code, get_current_babel_locale())


class ShopSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Shop)
    status = EnumField(ShopStatus)
    logo = serializers.SerializerMethodField()
    favicon = serializers.SerializerMethodField()
    contact_address = AddressSerializer(read_only=True)
    distance = serializers.SerializerMethodField()
    options = serializers.JSONField(binary=False, required=False)
    labels = LabelSerializer(many=True, required=False)

    class Meta:
        model = Shop
        kwargs = {
            "modified_on": {"read_only": True},
            "created_on": {"read_only": True},
        }
        exclude = ("identifier",)

    def to_representation(self, instance):
        data = super(ShopSerializer, self).to_representation(instance)
        data["currency"] = CurrencySerializer(Currency.objects.get(code=instance.currency), context=self.context).data
        return data

    def get_logo(self, shop):
        if shop.logo:
            return self.context["request"].build_absolute_uri(shop.logo.url)

    def get_favicon(self, shop):
        if shop.favicon:
            return self.context["request"].build_absolute_uri(shop.favicon.url)

    def get_distance(self, shop):
        return getattr(shop, 'distance', 0)


class ShopFilter(FilterSet):
    modified_before = django_filters.IsoDateTimeFilter(name="modified_on", lookup_expr='lt')
    modified_after = django_filters.IsoDateTimeFilter(name="modified_on", lookup_expr='gt')

    class Meta:
        model = Shop
        fields = ["id", "modified_before", "modified_after"]


class NearbyShopsFilter(filters.BaseFilterBackend):
    """
    This is intended to filter nearby shops within a small range.
    The farest the distance, the greater is the distance error.

    For a very precision, and cpu intensive, algorithm, you must use Vicenty:
    https://en.wikipedia.org/wiki/Vincenty%27s_formulae

    Can sort shops by:
        - `distance`

    Filter shops by:
    - a geographical area.
        Needs the `lat`, `lng` and `distance` parameters to perform the calculation.

    Sources:
        https://en.wikipedia.org/wiki/Decimal_degrees
        http://www.plumislandmedia.net/mysql/haversine-mysql-nearest-loc/
        http://stackoverflow.com/a/5237509 => what is the bounding box
    """
    DISTANCE_PER_DEGREE = 111.045   # 111.045km in a latitude degree

    def filter_queryset(self, request, queryset, view):
        latitude = float(request.query_params.get("lat", 0))
        longitude = float(request.query_params.get("lng", 0))
        distance = float(request.query_params.get("distance", 0))
        sort = request.query_params.get(api_settings.ORDERING_PARAM, "")

        if latitude and longitude:
            # create the distance field with the Harversie distance between the points
            # the trigonometry functions sin, cos, acos, radians and degrees must exist
            # in order to make this work. round the distance with 3 decimal places.
            query = """
            SELECT
                round(
                    degrees(
                        acos(
                            cos(radians(%s))
                            * cos(radians({address_table_name}.{latitude_field}))
                            * cos(radians(%s - {address_table_name}.{longitude_field}))
                            + sin(radians(%s))
                            * sin(radians({address_table_name}.{latitude_field}))
                        )
                    ) * %s
                , 3)
            FROM {address_table_name}
            WHERE {address_table_name}.{address_id_field}={shop_table_name}.{shop_contact_addr_id_field}
            """.format(
                address_table_name=Shop.contact_address.field.related_model._meta.db_table,
                latitude_field=Shop.contact_address.field.related_model._meta.get_field('latitude').name,
                longitude_field=Shop.contact_address.field.related_model._meta.get_field('longitude').name,
                address_id_field=Shop.contact_address.field.related_model._meta.get_field('id').name,
                shop_table_name=Shop._meta.db_table,
                shop_contact_addr_id_field=Shop.contact_address.field.column
            )

            queryset = queryset.annotate(
                distance=RawSQL(query, params=(latitude, longitude, latitude, self.DISTANCE_PER_DEGREE))
            )

            if distance:
                queryset = queryset.filter(distance__lte=distance)

            # sort by the calculated distance
            if sort.endswith("distance"):
                queryset = queryset.order_by(sort)

        return queryset


class ShopViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a shop by its ID.

    list: Lists all available shops.

    delete: Deletes a shop.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new shop.

    update: Fully updates an existing shop.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing shop.
    You can update only a set of attributes.
    """

    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, NearbyShopsFilter)
    filter_class = ShopFilter
    ordering_fields = ('modified_on',)

    def get_queryset(self):
        search_term = self.request.query_params.get('search')
        queryset = (Shop.objects
                    .prefetch_related('translations', 'staff_members')
                    .select_related('contact_address')
                    .all())
        if search_term:
            queryset = queryset.filter(translations__name__icontains=search_term)
        return queryset

    def get_view_name(self):
        return _("Shop")

    @classmethod
    def get_help_text(cls):
        return _("Shops can be listed, fetched, created, updated and deleted.")
