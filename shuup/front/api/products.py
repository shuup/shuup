# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from collections import defaultdict

import six
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils.translation import ugettext_lazy as _
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from shuup.api.mixins import PermissionHelperMixin
from shuup.core.models import (
    Category, get_person_contact, Product, ProductAttribute,
    ProductCrossSellType, ProductMode, ProductPackageLink, SalesUnit, Shop,
    ShopProduct, ShopProductVisibility
)
from shuup.core.pricing._context import PricingContext
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.utils.numbers import parse_decimal_string


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


class NormalProductSerializer(serializers.ModelSerializer):
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
            "sales_unit",
            "is_orderable",
            "cross_sell",
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
            cross_sell_data[key].append(NormalProductSerializer(cross_shop_product, context=self.context).data)

        return cross_sell_data


class CompleteProductSerializer(NormalProductSerializer):
    variations = serializers.SerializerMethodField()
    package_content = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    shop = ShopSerializer()

    class Meta(NormalProductSerializer.Meta):
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
            "cross_sell",
            "package_content",
            "distance"
        ]

    def get_variations(self, shop_product):
        shop_product_filter = FrontShopProductFilter()
        qs = ShopProduct.objects.filter(
            product__variation_parent=shop_product.product,
            shop=shop_product.shop,
        )
        variation_children = shop_product_filter.filter_queryset(self.context["request"], qs, None)
        return NormalProductSerializer(variation_children, many=True, context=self.context).data

    def get_package_content(self, shop_product):
        package_contents = []
        pkge_links = ProductPackageLink.objects.filter(parent=shop_product.product)
        for pkge_link in pkge_links:
            try:
                pkge_shop_product = pkge_link.parent.get_shop_instance(shop_product.shop)

                package_contents.append({
                    "quantity": pkge_link.quantity,
                    "product": NormalProductSerializer(pkge_shop_product, context=self.context).data
                })
            except ShopProduct.DoesNotExist:
                continue
        return package_contents

    def get_distance(self, shop_product):
        return getattr(shop_product, "distance", 0)


class FrontShopProductFilter(filters.BaseFilterBackend):
    """
    Filter shop products by visible or listed products and not deleted ones
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(
            visibility__in=(ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE),
            product__deleted=False
        ).distinct()


class ShopFilter(filters.BaseFilterBackend):
    """
    Filter shop products by shops.
    `shops` is a comma separed value: ?shops=1,2,3,4
    """
    def filter_queryset(self, request, queryset, view):
        shops = request.query_params.get("shops")
        if not shops:
            return queryset

        shop_filters = None
        for shop_id in shops.split(","):
            shop_filter = Q(shop__id=shop_id.strip())
            # make OR operator among all categories
            shop_filters = (shop_filter | shop_filters) if shop_filters else shop_filter

        if shop_filters:
            queryset = queryset.filter(shop_filters)
        return queryset


class ProductCategoryFilter(filters.BaseFilterBackend):
    """
    Filter shop products by categories IDs.
    `categories` is a comma separed value: ?categories=1,2,3,4
    """
    def filter_queryset(self, request, queryset, view):
        categories = request.query_params.get("categories")
        if not categories:
            return queryset

        category_filters = None
        for category in categories.split(","):
            category_filter = Q(categories__id=category.strip())
            # make OR operator among all categories
            category_filters = (category_filter | category_filters) if category_filters else category_filter

        if category_filters:
            queryset = queryset.filter(category_filters)
        return queryset


class ProductOrderingFilter(filters.BaseFilterBackend):
    """
    Order results by:
        - name
        - price
        - newest
        - shop
    """
    def filter_queryset(self, request, queryset, view):
        sort_field = request.query_params.get("sort", "").lower()
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


class NearByProductsFilter(filters.BaseFilterBackend):
    """
    Based of `shuup.core.api.shop.NearbyShopsFilter`
    """
    DISTANCE_PER_DEGREE = 111.045   # 111.045km in a latitude degree

    def filter_queryset(self, request, queryset, view):
        latitude = float(request.query_params.get("lat", 0))
        longitude = float(request.query_params.get("lng", 0))
        distance = float(request.query_params.get("distance", 0))
        sort = request.query_params.get("sort", "")

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
                distance=RawSQL(query, params=(latitude, longitude, latitude, self.DISTANCE_PER_DEGREE))
            )

            # only filter if user wants to
            if distance:
                queryset = queryset.filter(distance__lte=distance)

            # sort by the calculated distance
            if sort.endswith("distance"):
                queryset = queryset.order_by(sort)

        return queryset


class FrontProductViewSet(PermissionHelperMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list: Lists all available products to be used in storefront.
    """
    queryset = Product.objects.none()
    serializer_class = CompleteProductSerializer
    filter_backends = (
        FrontShopProductFilter, ProductOrderingFilter, ShopFilter, ProductCategoryFilter, NearByProductsFilter
    )

    def get_view_name(self):
        return _("Storefront Products")

    @classmethod
    def get_help_text(cls):
        return _("Storefront products can be listed and fetched.")

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
        serializer = CompleteProductSerializer(shop_products_qs, many=True, context={"request": request})
        return Response(serializer.data)
