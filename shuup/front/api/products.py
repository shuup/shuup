# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from collections import defaultdict

import six
from django.db.models.expressions import RawSQL
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.settings import api_settings

from shuup.api.mixins import PermissionHelperMixin
from shuup.core.models import (
    Category, get_person_contact, Product, ProductAttribute,
    ProductCrossSellType, ProductMode, ProductPackageLink, SalesUnit, Shop,
    ShopProduct, ShopProductVisibility
)
from shuup.core.pricing._context import PricingContext
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.utils.numbers import parse_decimal_string

DISTANCE_PER_DEGREE = 111.045   # 111.045km in a latitude degree


def make_comma_separated_list_fiter(filter_name, field_expression):
    """
    Create a filter which uses a comma-separated list of values to filter the queryset.

    :param str filter_name: the name of the query param to fetch values
    :param str field_expression: the field expression to filter the queryset, like `categories__in`
    """
    def filter_queryset(instance, request, queryset, view):
        values = request.query_params.get(filter_name)
        if not values:
            return queryset

        values = [v.strip() for v in values.split(",")]
        return queryset.filter(**{field_expression: values})

    attrs = {}
    attrs.setdefault("filter_queryset", filter_queryset)
    return type(str("CommaSeparatedIDListFilter"), (filters.BaseFilterBackend,), attrs)


class ShopSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    favicon = serializers.SerializerMethodField()

    def get_logo(self, shop):
        if shop.logo:
            return self.context["request"].build_absolute_uri(shop.logo.url)

    def get_favicon(self, shop):
        if shop.favicon:
            return self.context["request"].build_absolute_uri(shop.favicon.url)

    class Meta:
        model = Shop
        fields = ("id", "name", "logo", "favicon")


class SalesUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesUnit
        fields = ("name", "short_name", "decimals")


class AttributeSerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = ("name", "value", "identifier")

    def get_identifier(self, product_attribute):
        return product_attribute.attribute.identifier


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, category):
        if category.image:
            return self.context["request"].build_absolute_uri(category.image.url)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "image")


class CompleteShopProductSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    net_weight = serializers.SerializerMethodField()
    sales_unit = serializers.SerializerMethodField()
    is_orderable = serializers.SerializerMethodField()
    cross_sell = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()
    package_content = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    shop = ShopSerializer()

    class Meta:
        model = ShopProduct
        fields = [
            "id",
            "product_id",
            "name",
            "short_description",
            "description",
            "image",
            "categories",
            "attributes",
            "price",
            "net_weight",
            "variations",
            "shop",
            "is_orderable",
            "sales_unit",
            "cross_sell",
            "package_content",
            "distance"
        ]

    def _get_pricing_context(self, request, shop):
        customer = get_person_contact(request.user)
        return PricingContext(shop=shop, customer=customer)

    def get_product_id(self, shop_product):
        return shop_product.product_id

    def get_name(self, shop_product):
        return shop_product.product.name

    def get_short_description(self, shop_product):
        return shop_product.product.short_description

    def get_description(self, shop_product):
        return shop_product.product.description

    def get_image(self, shop_product):
        image = shop_product.product.primary_image
        if not image:
            return

        if image.external_url:
            return image.external_url
        elif image.file:
            return self.context["request"].build_absolute_uri(image.file.url)

    def get_categories(self, shop_product):
        return CategorySerializer(shop_product.categories.all_except_deleted(), many=True, context=self.context).data

    def get_attributes(self, shop_product):
        return AttributeSerializer(shop_product.product.attributes, many=True).data

    def get_price(self, shop_product):
        context = self._get_pricing_context(self.context["request"], shop_product.shop)
        return shop_product.product.get_price(context).value

    def get_net_weight(self, shop_product):
        return shop_product.product.net_weight

    def get_sales_unit(self, shop_product):
        return SalesUnitSerializer(shop_product.product.sales_unit).data

    def get_is_orderable(self, shop_product):
        customer = get_person_contact(self.context["request"].user)
        try:
            return shop_product.is_orderable(supplier=shop_product.suppliers.first(), customer=customer, quantity=1)
        except ShopProduct.DoesNotExist:
            return False

    def get_cross_sell(self, shop_product):
        cross_sell_data = {
            "recommended": [],
            "related": [],
            "computed": [],
            "bought_with": []
        }

        keys = {
            ProductCrossSellType.RECOMMENDED: "recommended",
            ProductCrossSellType.RELATED: "related",
            ProductCrossSellType.COMPUTED: "computed",
            ProductCrossSellType.BOUGHT_WITH: "bought_with",
        }

        customer = get_person_contact(self.context["request"].user)
        for cross_sell in shop_product.product.cross_sell_1.all():
            try:
                cross_shop_product = cross_sell.product2.get_shop_instance(shop_product.shop)
            except ShopProduct.DoesNotExist:
                continue

            supplier = cross_shop_product.suppliers.first()
            quantity = cross_shop_product.minimum_purchase_quantity

            if not cross_shop_product.is_orderable(supplier=supplier, customer=customer, quantity=quantity):
                continue

            key = keys[cross_sell.type]
            cross_sell_data[key].append(NormalShopProductSerializer(cross_shop_product, context=self.context).data)

        return cross_sell_data

    def get_variations(self, shop_product):
        data = []
        combinations = list(shop_product.product.get_all_available_combinations() or [])
        if not combinations and shop_product.product.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            for product_pk, sku in Product.objects.filter(
                    variation_parent_id=shop_product.product_id).values_list("pk", "sku"):
                combinations.append({
                    "result_product_pk": product_pk,
                    "sku_part": sku,
                    "hash": None,
                    "variable_to_value": {}
                })

        for combination in combinations:
            child = ShopProduct.objects.filter(
                shop_id=shop_product.shop.id, product__pk=combination["result_product_pk"]).first()
            data.append({
                "product": NormalShopProductSerializer(child, many=False, context=self.context).data,
                "sku_part": combination["sku_part"],
                "hash": combination["hash"],
                "combination": {
                    force_text(k): force_text(v) for k, v in six.iteritems(combination["variable_to_value"])
                }
            })
        return data

    def get_package_content(self, shop_product):
        package_contents = []
        pkge_links = ProductPackageLink.objects.filter(parent=shop_product.product)
        for pkge_link in pkge_links:
            try:
                pkge_shop_product = pkge_link.parent.get_shop_instance(shop_product.shop)

                package_contents.append({
                    "quantity": pkge_link.quantity,
                    "product": NormalShopProductSerializer(pkge_shop_product, context=self.context).data
                })
            except ShopProduct.DoesNotExist:
                continue
        return package_contents

    def get_distance(self, shop_product):
        return getattr(shop_product, "distance", 0)


class NormalShopProductSerializer(CompleteShopProductSerializer):
    class Meta(CompleteShopProductSerializer.Meta):
        fields = [
            "id",
            "product_id",
            "name",
            "short_description",
            "description",
            "image",
            "categories",
            "attributes",
            "price",
            "net_weight",
            "sales_unit",
            "is_orderable",
            "cross_sell",
        ]


class FrontShopProductFilter(filters.BaseFilterBackend):
    """
    Filter shop products by visible or listed products and not deleted ones
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(
            visibility__in=(ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE),
            product__deleted=False
        ).distinct()


class ShopProductOrderingFilter(filters.BaseFilterBackend):
    """
    Order results by:
        - name
        - price
        - newest
        - shop
    """
    def filter_queryset(self, request, queryset, view):
        sort_field = request.query_params.get(api_settings.ORDERING_PARAM, "").lower()
        order = "-" if sort_field.startswith("-") else ""

        if sort_field.endswith("name"):
            sort_field = "product__translations__name"
        elif sort_field.endswith("price"):
            sort_field = "default_price_value"
        elif sort_field.endswith("newest"):
            order = "-"
            sort_field = "product__created_on"
        elif sort_field.endswith("shops"):
            sort_field = "shops"
        else:
            # unknown field
            sort_field = ""

        if sort_field:
            queryset = queryset.order_by("{}{}".format(order, sort_field))
        return queryset


class NearByShopProductFilter(filters.BaseFilterBackend):
    """
    Based of `shuup.core.api.shop.NearbyShopsFilter`
    """
    def filter_queryset(self, request, queryset, view):
        latitude = float(request.query_params.get("lat", 0))
        longitude = float(request.query_params.get("lng", 0))
        distance = float(request.query_params.get("distance", 0))
        sort = request.query_params.get(api_settings.ORDERING_PARAM, "")

        if latitude and longitude:
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
            INNER JOIN {shop_table_name} ON (
                {address_table_name}.{address_id_field}={shop_table_name}.{shop_contact_addr_id_field}
            )
            WHERE {shop_table_name}.{shop_id_field}={shopproduct_table_name}.{shopproduct_shop_id_field}
            """.format(
                address_table_name=Shop.contact_address.field.related_model._meta.db_table,
                latitude_field=Shop.contact_address.field.related_model._meta.get_field('latitude').name,
                longitude_field=Shop.contact_address.field.related_model._meta.get_field('longitude').name,
                address_id_field=Shop.contact_address.field.related_model._meta.get_field('id').name,
                shop_table_name=Shop._meta.db_table,
                shop_id_field=Shop._meta.get_field('id').name,
                shop_contact_addr_id_field=Shop.contact_address.field.column,
                shopproduct_table_name=ShopProduct._meta.db_table,
                shopproduct_shop_id_field=ShopProduct.shop.field.column,
            )

            queryset = queryset.select_related("shop").annotate(
                distance=RawSQL(query, params=(latitude, longitude, latitude, DISTANCE_PER_DEGREE))
            )

            # only filter if user wants to
            if distance:
                queryset = queryset.filter(distance__lte=distance)

            # sort by the calculated distance
            if sort.endswith("distance"):
                queryset = queryset.order_by(sort)

        return queryset


class FrontShopProductViewSet(PermissionHelperMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list: Lists all available shop products to be used in storefront.
    """
    queryset = ShopProduct.objects.none()
    serializer_class = CompleteShopProductSerializer
    filter_backends = (
        FrontShopProductFilter,
        ShopProductOrderingFilter,
        NearByShopProductFilter,
        make_comma_separated_list_fiter("id", "id__in"),
        make_comma_separated_list_fiter("shops", "shop__id__in"),
        make_comma_separated_list_fiter("products", "product__id__in"),
        make_comma_separated_list_fiter("categories", "categories__id__in"),
    )

    def get_view_name(self):
        return _("Storefront Shop Products")

    @classmethod
    def get_help_text(cls):
        return _("Storefront shop products can be listed and fetched.")

    def get_queryset(self):
        return ShopProduct.objects.select_related(
            "product", "product__primary_image", "product__sales_unit", "shop__contact_address"
        ).prefetch_related("suppliers", "product__cross_sell_1").filter(
            product__variation_parent__isnull=True,
            product__mode__in=(
                ProductMode.NORMAL,
                ProductMode.VARIABLE_VARIATION_PARENT,
                ProductMode.SIMPLE_VARIATION_PARENT,
                ProductMode.PACKAGE_PARENT
            )
        )

    @list_route(methods=['get'])
    def best_selling(self, request):
        """
        Returns the top 20 (default) best selling products.
        To change the number of products, set the `limit` query param.
        """
        limit = int(parse_decimal_string(request.query_params.get("limit", 20)))
        best_selling_products = get_best_selling_product_info(shop_ids=[request.shop.pk])
        combined_variation_products = defaultdict(int)

        for product_id, parent_id, qty in best_selling_products:
            if parent_id:
                combined_variation_products[parent_id] += qty
            else:
                combined_variation_products[product_id] += qty

        # take here the top `limit` records, because the filter_queryset below can mess with our work
        product_ids = [
            d[0] for d in sorted(six.iteritems(combined_variation_products), key=lambda i: i[1], reverse=True)[:limit]
        ]

        shop_products_qs = ShopProduct.objects.filter(product__id__in=product_ids)
        shop_products_qs = self.filter_queryset(shop_products_qs).distinct()
        serializer = CompleteShopProductSerializer(shop_products_qs, many=True, context={"request": request})
        return Response(serializer.data)


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    attributes = AttributeSerializer(many=True)
    sales_unit = SalesUnitSerializer()
    shop_products = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    categories = serializers.SerializerMethodField()
    closest_shop_distance = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "short_description",
            "description",
            "image",
            "attributes",
            "net_weight",
            "sales_unit",
            "shop_products",
            "categories",
            "closest_shop_distance"
        ]

    def get_categories(self, product):
        # get all categories which is related to this product, no matter what shop
        categories = Category.objects.all_except_deleted().filter(shop_products__product=product).distinct()
        return CategorySerializer(categories, many=True, context=self.context).data

    def get_image(self, product):
        image = product.primary_image
        if not image:
            return

        if image.external_url:
            return image.external_url
        elif image.file:
            return self.context["request"].build_absolute_uri(image.file.url)

    def get_closest_shop_distance(self, product):
        return getattr(product, "closest_shop_distance", 0)


class ClosestShopFilter(filters.BaseFilterBackend):
    """
    Add a field using subquery to get the closest shop distance
    Based of `shuup.core.api.shop.NearbyShopsFilter`
    """
    def filter_queryset(self, request, queryset, view):
        latitude = float(request.query_params.get("lat", 0))
        longitude = float(request.query_params.get("lng", 0))
        distance = float(request.query_params.get("distance", 0))
        sort = request.query_params.get(api_settings.ORDERING_PARAM, "")

        if latitude and longitude:
            query = """
            SELECT MIN(
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
                , 3))
            FROM {address_table_name}
            INNER JOIN {shop_table_name} ON (
                {address_table_name}.{address_id_field}={shop_table_name}.{shop_contact_addr_id_field}
            )
            INNER JOIN {shopproduct_table_name} ON (
                {shop_table_name}.{shop_id_field}={shopproduct_table_name}.{shopproduct_shop_id_field}
            )
            WHERE {shopproduct_table_name}.{shopproduct_product_id_field}={product_table_name}.{product_id_field}
            """.format(
                address_table_name=Shop.contact_address.field.related_model._meta.db_table,
                latitude_field=Shop.contact_address.field.related_model._meta.get_field('latitude').name,
                longitude_field=Shop.contact_address.field.related_model._meta.get_field('longitude').name,
                address_id_field=Shop.contact_address.field.related_model._meta.get_field('id').name,
                shop_table_name=Shop._meta.db_table,
                shop_id_field=Shop._meta.get_field('id').name,
                shop_contact_addr_id_field=Shop.contact_address.field.column,
                shopproduct_table_name=ShopProduct._meta.db_table,
                shopproduct_shop_id_field=ShopProduct.shop.field.column,
                shopproduct_product_id_field=ShopProduct.product.field.column,
                product_table_name=Product._meta.db_table,
                product_id_field=Product._meta.get_field('id').name
            )

            queryset = queryset.annotate(
                closest_shop_distance=RawSQL(query, params=(latitude, longitude, latitude, DISTANCE_PER_DEGREE))
            )

            # show products in range
            if distance:
                queryset = queryset.filter(closest_shop_distance__lte=distance)

            # sort by the calculated distance
            if sort.endswith("distance"):
                order = "-" if sort.startswith("-") else ""
                queryset = queryset.order_by("{}closest_shop_distance".format(order))

        return queryset


class ProductOrderingFilter(filters.BaseFilterBackend):
    """
    Order results by:
        - name
        - newest
    """
    def filter_queryset(self, request, queryset, view):
        sort_field = request.query_params.get(api_settings.ORDERING_PARAM, "").lower()
        order = "-" if sort_field.startswith("-") else ""

        if sort_field.endswith("name"):
            sort_field = "translations__name"
        elif sort_field.endswith("newest"):
            order = "-"
            sort_field = "created_on"
        else:
            # unknown field
            sort_field = ""

        if sort_field:
            queryset = queryset.order_by("{}{}".format(order, sort_field))
        return queryset


class FrontProductViewSet(PermissionHelperMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list: Lists all products to be used in storefront.
    """
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    filter_backends = (
        ClosestShopFilter,
        ProductOrderingFilter,
        make_comma_separated_list_fiter("id", "id__in"),
        make_comma_separated_list_fiter("categories", "shop_products__categories__id__in"),
    )

    def get_view_name(self):
        return _("Storefront Products")

    @classmethod
    def get_help_text(cls):
        return _("Storefront products can be listed and fetched.")

    def get_queryset(self):
        return Product.objects.all_except_deleted().select_related(
            "primary_image", "sales_unit"
        ).filter(
            variation_parent__isnull=True,
            mode__in=(
                ProductMode.NORMAL,
                ProductMode.VARIABLE_VARIATION_PARENT,
                ProductMode.SIMPLE_VARIATION_PARENT,
                ProductMode.PACKAGE_PARENT
            ),
            shop_products__visibility__in=(ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE),
        ).distinct()
