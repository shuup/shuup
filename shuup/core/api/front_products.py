# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import defaultdict

import six
from django.db.models import Prefetch
from django.db.models.expressions import RawSQL
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.settings import api_settings

from shuup.api.fields import FormattedDecimalField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.models import (
    Category, get_person_contact, Product, ProductAttribute,
    ProductCrossSellType, ProductMode, ProductPackageLink, SalesUnit, Shop,
    ShopProduct, ShopProductVisibility, ShopStatus
)
from shuup.core.pricing._context import PricingContext
from shuup.core.utils import context_cache
from shuup.core.utils.prices import convert_taxness
from shuup.core.utils.product_statistics import get_best_selling_product_info

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


def get_shop_product_queryset(parents_only=True):
    qs = ShopProduct.objects.select_related(
        "shop", "product", "product__sales_unit", "product__primary_image", "product__primary_image__file"
    ).prefetch_related(
        "product__translations", "shop__translations", "product__sales_unit__translations", "suppliers"
    ).prefetch_related(
        Prefetch(
            "categories",
            queryset=Category.objects.all_except_deleted().prefetch_related("translations")
        )
    ).prefetch_related(
        Prefetch(
            "product__attributes",
            queryset=ProductAttribute.objects.all().prefetch_related("attribute", "attribute__translations")
        )
    ).filter(shop__status=ShopStatus.ENABLED)

    if parents_only:
        qs = qs.filter(
            product__variation_parent__isnull=True,
            product__mode__in=(
                ProductMode.NORMAL,
                ProductMode.VARIABLE_VARIATION_PARENT,
                ProductMode.SIMPLE_VARIATION_PARENT,
                ProductMode.PACKAGE_PARENT
            )
        )
    return qs


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


class PricefulSerializer(serializers.Serializer):
    base_price = FormattedDecimalField(source='base_price.value', coerce_to_string=False)
    price = FormattedDecimalField(source='price.value', coerce_to_string=False)
    discount_amount = FormattedDecimalField(source='discount_amount.value', required=False, coerce_to_string=False)
    discount_rate = FormattedDecimalField(required=False, coerce_to_string=False)
    discount_percentage = FormattedDecimalField(required=False, coerce_to_string=False)
    taxful_price = FormattedDecimalField(source='taxful_price.value', required=False, coerce_to_string=False)
    taxless_price = FormattedDecimalField(source='taxless_price.value', required=False, coerce_to_string=False)
    taxful_base_price = FormattedDecimalField(
        source='taxful_base_price.value', required=False, coerce_to_string=False)
    taxless_base_price = FormattedDecimalField(
        source='taxless_base_price.value', required=False, coerce_to_string=False)
    tax_amount = FormattedDecimalField(source='tax_amount.value', required=False, coerce_to_string=False)
    is_discounted = serializers.BooleanField()

    class Meta:
        fields = "__all__"


class CompleteShopProductSerializer(serializers.ModelSerializer):
    product_id = serializers.ReadOnlyField()
    name = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    primary_category = CategorySerializer()
    categories = CategorySerializer(many=True)
    attributes = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()
    net_weight = serializers.ReadOnlyField(source='product.net_weight')
    sales_unit = serializers.SerializerMethodField()
    is_orderable = serializers.SerializerMethodField()
    cross_sell = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()
    package_content = serializers.SerializerMethodField()
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
            "primary_category",
            "categories",
            "attributes",
            "price",
            "price_info",
            "net_weight",
            "variations",
            "shop",
            "is_orderable",
            "sales_unit",
            "cross_sell",
            "package_content"
        ]

    @property
    def children_serializer(self):
        return NormalShopProductSerializer

    def get_name(self, shop_product):
        return shop_product.get_name()

    def get_description(self, shop_product):
        return shop_product.get_description()

    def get_short_description(self, shop_product):
        return shop_product.get_short_description()

    def _get_pricing_context(self, request, shop):
        return PricingContext(shop=shop, customer=self.context["customer"])

    def get_image(self, shop_product):
        image = shop_product.product.primary_image
        if not image:
            return

        if image.external_url:
            return image.external_url
        elif image.file:
            return self.context["request"].build_absolute_uri(image.file.url)

    def get_attributes(self, shop_product):
        return AttributeSerializer(shop_product.product.attributes, many=True).data

    def _get_product_price_info(self, shop_product):
        context = self._get_pricing_context(self.context["request"], shop_product.shop)
        price_info = shop_product.product.get_price_info(context)
        return convert_taxness(self.context["request"], shop_product.product, price_info, True)

    def _get_cached_product_price_info(self, shop_product):
        key, val = context_cache.get_cached_value(identifier="shop_product_price_info",
                                                  item=shop_product,
                                                  context={"customer": self.context["customer"]},
                                                  allow_cache=True)
        if val is not None:
            return val

        price_info = self._get_product_price_info(shop_product)
        context_cache.set_cached_value(key, price_info)
        return price_info

    def get_price_info(self, shop_product):
        price_info = self._get_cached_product_price_info(shop_product)
        return PricefulSerializer(price_info).data

    def get_price(self, shop_product):
        price_info = self._get_cached_product_price_info(shop_product)
        return price_info.price.value

    def get_net_weight(self, shop_product):
        return shop_product.product.net_weight

    def get_sales_unit(self, shop_product):
        return SalesUnitSerializer(shop_product.product.sales_unit).data

    def get_is_orderable(self, shop_product):
        suppliers = shop_product.suppliers.enabled()
        if len(suppliers) == 0:
            return False
        try:
            return shop_product.is_orderable(supplier=suppliers[0], customer=self.context["customer"], quantity=1)
        except ShopProduct.DoesNotExist:
            return False
        return False

    def _get_cross_sell(self, shop_product):
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
        customer = self.context["customer"]
        for cross_sell in shop_product.product.cross_sell_1.all():
            try:
                cross_shop_product = cross_sell.product2.get_shop_instance(shop_product.shop)
            except ShopProduct.DoesNotExist:
                continue

            quantity = cross_shop_product.minimum_purchase_quantity
            supplier = cross_shop_product.get_supplier(customer, quantity)

            if not cross_shop_product.is_orderable(supplier=supplier, customer=customer, quantity=quantity):
                continue

            key = keys[cross_sell.type]
            cross_sell_data[key].append(self.children_serializer(cross_shop_product, context=self.context).data)
        return cross_sell_data

    def get_cross_sell(self, shop_product):
        key, val = context_cache.get_cached_value(identifier="cross_sell",
                                                  item=shop_product,
                                                  context={"customer": self.context["customer"]},
                                                  allow_cache=True)
        if val is not None:
            return val

        cross_sell_data = self._get_cross_sell(shop_product)
        context_cache.set_cached_value(key, cross_sell_data)
        return cross_sell_data

    def _get_variations(self, shop_product):
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

        qs = get_shop_product_queryset(False).filter(
            shop_id=shop_product.shop_id, product__pk__in=[combo["result_product_pk"] for combo in combinations])
        products = self.children_serializer(qs, many=True, context=self.context).data
        product_map = {product["product_id"]: product for product in products}
        for combination in combinations:
            child = product_map.get(combination["result_product_pk"])
            data.append({
                "product": child or {},
                "sku_part": combination["sku_part"],
                "hash": combination["hash"],
                "combination": {
                    force_text(k): force_text(v) for k, v in six.iteritems(combination["variable_to_value"])
                }
            })
        return data

    def get_variations(self, shop_product):
        key, val = context_cache.get_cached_value(identifier="variations",
                                                  item=shop_product,
                                                  context={"customer": self.context["customer"]},
                                                  allow_cache=True)
        if val is not None:
            return val

        variations = self._get_variations(shop_product)
        context_cache.set_cached_value(key, variations)
        return variations

    def _get_package_content(self, shop_product):
        package_contents = []
        pkge_links = ProductPackageLink.objects.filter(parent=shop_product.product)
        for pkge_link in pkge_links:
            try:
                pkge_shop_product = pkge_link.parent.get_shop_instance(shop_product.shop)

                package_contents.append({
                    "quantity": pkge_link.quantity,
                    "product": self.children_serializer(pkge_shop_product, context=self.context).data
                })
            except ShopProduct.DoesNotExist:
                continue
        return package_contents

    def get_package_content(self, shop_product):
        key, val = context_cache.get_cached_value(identifier="package_contents",
                                                  item=shop_product,
                                                  context={"customer": self.context["customer"]},
                                                  allow_cache=True)
        if val is not None:
            return val

        package_contents = self._get_package_content(shop_product)
        context_cache.set_cached_value(key, package_contents)
        return package_contents


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
            "price_info",
            "net_weight",
            "sales_unit",
            "is_orderable",
            "cross_sell",
        ]


class FrontShopProductFilter(filters.BaseFilterBackend):
    """
    Filter shop products by visible or listed products and not deleted ones.
    You can also filter by:
        - shop - the ID of the shop
    """
    def filter_queryset(self, request, queryset, view):
        shop = request.query_params.get("shop")

        shops_qs = queryset.filter(
            visibility__in=(ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE),
            product__deleted=False
        )

        # filter by shop
        if shop:
            shops_qs = shops_qs.filter(shop_id=shop)

        return shops_qs


class ShopProductOrderingFilter(filters.BaseFilterBackend):
    """
    Order results by:
        - name
        - price
        - newest
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
        else:
            # unknown field
            sort_field = ""

        if sort_field:
            queryset = queryset.order_by("{}{}".format(order, sort_field))
        return queryset


class FrontShopProductViewSet(PermissionHelperMixin,
                              mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    """
    list: Lists all available shop products to be used in storefront.
    """
    queryset = ShopProduct.objects.none()
    serializer_class = CompleteShopProductSerializer
    filter_backends = (
        FrontShopProductFilter,
        ShopProductOrderingFilter,
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

    def get_serializer_context(self):
        ctx = super(FrontShopProductViewSet, self).get_serializer_context()
        ctx["customer"] = get_person_contact(self.request.user)
        return ctx

    def get_queryset(self):
        return get_shop_product_queryset()

    @list_route(methods=['get'])
    def best_selling(self, request):
        best_selling_products = get_best_selling_product_info(
            shop_ids=[request.GET.get("shop", Shop.objects.first().pk)])
        combined_variation_products = defaultdict(int)

        for product_id, parent_id, qty in best_selling_products:
            if parent_id:
                combined_variation_products[parent_id] += qty
            else:
                combined_variation_products[product_id] += qty

        # take here the top `limit` records, because the filter_queryset below can mess with our work
        product_ids = [
            d[0] for d in sorted(six.iteritems(combined_variation_products), key=lambda i: i[1], reverse=True)
        ]

        shop_products_qs = ShopProduct.objects.filter(product__id__in=product_ids)
        shop_products_qs = self.filter_queryset(shop_products_qs).distinct()
        page = self.paginate_queryset(shop_products_qs)
        if page is not None:
            serializer = self.get_serializer_class()(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer_class()(shop_products_qs, many=True, context=self.get_serializer_context())
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
        ProductOrderingFilter,
        ClosestShopFilter,
        make_comma_separated_list_fiter("id", "id__in"),
        make_comma_separated_list_fiter("categories", "shop_products__categories__id__in"),
    )

    def get_view_name(self):
        return _("Storefront Products")

    @classmethod
    def get_help_text(cls):
        return _("Storefront products can be listed and fetched.")

    def get_queryset(self):
        return Product.objects.all_except_deleted().prefetch_related(
            "attributes", "translations", "shop_products", "media"
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
