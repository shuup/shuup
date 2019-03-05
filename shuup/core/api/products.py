# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import django_filters
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import filters, mixins, serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.api.product_media import (
    ProductMediaSerializer, ProductMediaUploadSerializer
)
from shuup.core.excs import ImpossibleProductModeException
from shuup.core.models import (
    Product, ProductAttribute, ProductPackageLink, ProductType,
    ProductVariationResult, ProductVisibility, ShippingMode, ShopProduct,
    ShopProductVisibility, Supplier
)
from shuup.utils.numbers import parse_decimal_string

from .product_variation import (
    ProductLinkVariationVariableSerializer, ProductSimpleVariationSerializer,
    ProductVariationVariableResultSerializer
)


class ShopProductSerializer(TranslatableModelSerializer):
    orderable = serializers.SerializerMethodField()
    visibility = EnumField(enum=ShopProductVisibility)
    visibility_limit = EnumField(enum=ProductVisibility)
    translations = TranslatedFieldsField(shared_model=ShopProduct, required=False)

    class Meta:
        model = ShopProduct
        fields = "__all__"
        extra_kwargs = {
            "visibility_groups": {"required": False},
            "shipping_methods": {"required": False},
            "suppliers": {"required": False},
            "payment_methods": {"required": False},
            "categories": {"required": False},
        }

    def get_orderable(self, shop_product):
        customer = self.context["request"].customer
        quantity = shop_product.minimum_purchase_quantity
        supplier = shop_product.get_supplier(customer, quantity)
        try:
            return shop_product.is_orderable(supplier=supplier, customer=customer, quantity=quantity)
        except:
            return False


class ProductAttributeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ProductAttribute, required=False)

    class Meta:
        fields = "__all__"
        model = ProductAttribute
        extra_kwargs = {
            "product": {"read_only": True}
        }


class ProductTypeSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ProductType)

    class Meta:
        fields = "__all__"
        model = ProductType


class ProductPackageLinkSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        fields = ("quantity", "product", "id")
        extra_kwargs = {
            "id": {"read_only": True}
        }
        model = ProductPackageLink

    def get_product(self, product_pkge_link):
        return product_pkge_link.child.pk


class ProductPackageChildSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=36, decimal_places=9)


class ShopProductSubsetSerializer(ShopProductSerializer):
    """ A subset class to hide id and product fields """
    class Meta:
        model = ShopProduct
        extra_kwargs = {
            "visibility_groups": {"required": False},
            "shipping_methods": {"required": False},
            "suppliers": {"required": False},
            "payment_methods": {"required": False},
            "categories": {"required": False},
        }
        exclude = ("id", "product")


class ProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    shop_products = ShopProductSubsetSerializer(many=True, required=False)
    primary_image = ProductMediaSerializer(read_only=True)
    media = ProductMediaSerializer(read_only=True, many=True)
    shipping_mode = EnumField(enum=ShippingMode)
    attributes = ProductAttributeSerializer(many=True, required=False)
    package_content = serializers.SerializerMethodField()
    variation_children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    variation_variables = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    variation_results = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = Product
        extra_kwargs = {
            "mode": {"read_only": True},
            "variation_parent": {"read_only": True},
            "created_on": {"read_only": True},
            "modified_on": {"read_only": True},
            "deleted_on": {"read_only": True}
        }

    def get_package_content(self, product):
        return ProductPackageLinkSerializer(ProductPackageLink.objects.filter(parent=product), many=True).data

    def get_variation_results(self, product):
        return ProductVariationVariableResultSerializer(product).data["combinations"]

    def create(self, validated_data):
        nested = self._pop_nested_objects(validated_data)
        instance = super(ProductSerializer, self).create(validated_data)
        self._handle_nested_structures(instance, nested)
        return instance

    def update(self, instance, validated_data):
        nested = self._pop_nested_objects(validated_data)
        super(ProductSerializer, self).update(instance, validated_data)
        self._handle_nested_structures(instance, nested)
        return instance

    def _pop_nested_objects(self, validated_data):
        return {
            field: validated_data.pop(field, None)
            for field in ['attributes', 'shop_products']
        }

    def _handle_nested_structures(self, product, nested):
        attributes = nested['attributes']
        shop_products = nested['shop_products']

        if not self.partial:
            if attributes is not None:
                product.attributes.all().delete()
            if shop_products is not None:
                product.shop_products.all().delete()

        if attributes:
            for attribute_data in attributes:
                self._handle_attribute_value(product, attribute_data)

        if shop_products:
            for shop_product_data in shop_products:
                self._handle_shop_product(product, shop_product_data)

    def _handle_attribute_value(self, product, data):
        attr = data["attribute"]  # type: shuup.core.models.Attribute
        if attr.is_stringy and attr.is_translated:
            translations = data.get('translations')
            if not self.partial or translations is None:
                product.clear_attribute_value(attr.identifier)
            for (lang, lang_data) in (translations or {}).items():
                value = lang_data["translated_string_value"]
                product.set_attribute_value(attr.identifier, value, language=lang)
        elif attr.is_stringy:
            product.set_attribute_value(attr.identifier, data["untranslated_string_value"])
        elif attr.is_numeric:
            product.set_attribute_value(attr.identifier, data["numeric_value"])
        elif attr.is_temporal:
            product.set_attribute_value(attr.identifier, data["datetime_value"])

    def _handle_shop_product(self, product, data):
        shop = data.pop('shop')
        m2m_data = [
            (field, data.pop(field, None))
            for field in ['suppliers', 'categories', 'visibility_groups',
                          'shipping_methods', 'payment_methods']
        ]

        (shop_product, created) = ShopProduct.objects.get_or_create(
            product=product, shop=shop, defaults=data)

        if not created:
            for (field, value) in data.items():
                setattr(shop_product, field, value)
            shop_product.save()

        for (field, values) in m2m_data:
            if values is None:
                continue
            field_objects = getattr(shop_product, field)
            field_objects.clear()
            for value in values:
                field_objects.add(value)

        return shop_product


class ProductStockStatusSerializer(serializers.Serializer):
    stocks = serializers.SerializerMethodField()

    def get_stocks(self, product):
        stocks = []
        supplier_qs = Supplier.objects.enabled().filter(shop_products__product=product).distinct()

        # filtered by supplier
        supplier_id = int(parse_decimal_string(self.context["request"].query_params.get("supplier", 0)))
        if supplier_id:
            supplier_qs = supplier_qs.filter(pk=supplier_id)

        for supplier in supplier_qs:
            stock_status = supplier.get_stock_status(product.id)

            stocks.append({
                "id": supplier.id,
                "name": supplier.name,
                "type": supplier.type,
                "logical_count": stock_status.logical_count,
                "physical_count": stock_status.physical_count,
                "message": stock_status.message,
                "error": stock_status.error
            })

        return {
            "product": product.id,
            "sku": product.sku,
            "stocks": stocks
        }

    def to_representation(self, obj):
        # flatten data
        return super(ProductStockStatusSerializer, self).to_representation(obj).get("stocks")


class ProductFilter(FilterSet):
    product = django_filters.NumberFilter(name="pk", lookup_expr="exact")
    sku = django_filters.CharFilter(name="sku", lookup_expr="exact")
    supplier = django_filters.ModelChoiceFilter(name="shop_products__suppliers",
                                                queryset=Supplier.objects.enabled(),
                                                lookup_expr="exact")

    class Meta:
        model = Product
        fields = ["id", "product", "sku", "supplier"]


class ProductViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a product by its ID.

    list: Lists all available products.

    delete: Deletes a product.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new product.

    update: Fully updates an existing product.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product.
    You can update only a set of attributes.
    """

    queryset = Product.objects.all_except_deleted()
    serializer_class = ProductSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filter_class = ProductFilter

    def get_view_name(self):
        return _("Products")

    @classmethod
    def get_help_text(cls):
        return _("Products can be listed, fetched, created, updated and deleted.")

    def perform_destroy(self, instance):
        instance.soft_delete(self.request.user)

    @schema_serializer_class(ShopProductSubsetSerializer)
    @detail_route(methods=['post'])
    def add_shop(self, request, pk=None):
        """
        Adds a new shop to a product.
        If the shop relation already exists, an error will be returned.
        """
        product = self.get_object()
        serializer = ShopProductSubsetSerializer(data=request.data)

        if serializer.is_valid():
            shop_product = ShopProduct.objects.filter(shop=serializer.validated_data["shop"],
                                                      product=product).first()

            if not shop_product:
                shop_product = serializer.save(product=product)
                return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(ProductMediaUploadSerializer)
    @detail_route(methods=['post'])
    def add_media(self, request, pk=None):
        """
        Adds a media to a product.
        The image must be serialized in base64 and sent using a Data URI scheme:
        https://en.wikipedia.org/wiki/Data_URI_scheme
        """
        product = self.get_object()
        serializer = ProductMediaUploadSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save(product=product)
            return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(ProductAttributeSerializer)
    @detail_route(methods=['post'])
    def add_attribute(self, request, pk=None):
        """
        Adds an attribute value to a product.
        The attribute must be related with the product type.
        """
        product = self.get_object()
        serializer = ProductAttributeSerializer(data=request.data)

        if serializer.is_valid():
            # attribute does not belong to the product type
            if not product.type.attributes.filter(id=serializer.validated_data["attribute"].pk).exists():
                return Response({"error": "Attribute does not belong to the product type."},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer.save(product=product)
            return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(ProductPackageChildSerializer)
    @detail_route(methods=['post'])
    def make_package(self, request, pk=None):
        """
        Convert this product into a package of products.
        Send a list of products and quantities which will be the package contents.
        """
        product = self.get_object()
        serializer = ProductPackageChildSerializer(data=request.data, many=True)

        if serializer.is_valid():
            package_def = {package["product"]: package["quantity"] for package in serializer.validated_data}

            try:
                product.make_package(package_def)
            except ImpossibleProductModeException as exc:
                return Response("{}".format(exc), status=status.HTTP_400_BAD_REQUEST)
            else:
                product.save()
                return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['get'])
    def stocks(self, request):
        """
        Retrieves a list of products and their stocks.
        You can filter the items using the `sku`, `product` and `supplier` parameters.
        """
        product_qs = self.filter_queryset(self.get_queryset()).distinct()
        context = {'request': request}
        page = self.paginate_queryset(product_qs)
        serializer = ProductStockStatusSerializer((page or product_qs), many=True, context=context)
        return Response(serializer.data)

    @schema_serializer_class(ProductSimpleVariationSerializer)
    @detail_route(methods=['post', 'delete'])
    def simple_variation(self, request, pk=None):
        """
        Add or remove simple variations of the product.
        Send a list of products to be added or removed.
        """
        product = self.get_object()
        serializer = ProductSimpleVariationSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            if request.method == "POST":
                created = False
                for child_product in serializer.validated_data["products"]:
                    child_product.link_to_parent(product)
                    created = True

                return Response(status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK))

            elif request.method == "DELETE":
                for child_product in serializer.validated_data["products"]:
                    child_product.variation_parent = None
                    child_product.verify_mode()
                    child_product.save()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(ProductLinkVariationVariableSerializer)
    @detail_route(methods=['post', 'delete', 'put'])
    def variable_variation(self, request, pk=None):
        """
        Add, update or remove variable variation of the product.
        Send a single product to be related as a variable variation.
        """
        product = self.get_object()
        serializer = ProductLinkVariationVariableSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():

            if request.method == "POST":
                ProductVariationResult.objects.create(product=product,
                                                      combination_hash=serializer.validated_data["hash"],
                                                      status=serializer.validated_data.get("status"),
                                                      result=serializer.validated_data["product"])
                product.verify_mode()
                product.save()
                return Response(status=status.HTTP_201_CREATED)

            elif request.method == "PUT":
                try:
                    result = ProductVariationResult.objects.get(product=product,
                                                                combination_hash=serializer.validated_data["hash"])
                except ProductVariationResult.DoesNotExist:
                    return Response(data={"error": "Combination not found"}, status=status.HTTP_404_NOT_FOUND)

                if serializer.validated_data.get("status"):
                    result.status = serializer.validated_data["status"]

                result.result = serializer.validated_data["product"]
                result.save()
                return Response(status=status.HTTP_200_OK)

            elif request.method == "DELETE":
                try:
                    result = ProductVariationResult.objects.get(product=product,
                                                                combination_hash=serializer.validated_data["hash"])
                except ProductVariationResult.DoesNotExist:
                    return Response(data={"error": "Combination not found"}, status=status.HTTP_404_NOT_FOUND)

                result.delete()
                product.verify_mode()
                product.save()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopProductViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a shop product by its ID.

    list: Lists all available products.

    delete: Deletes a shop product.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new shop product.

    update: Fully updates an existing shop product.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing shop product.
    You can update only a set of attributes.
    """

    queryset = ShopProduct.objects.none()
    serializer_class = ShopProductSerializer

    def get_queryset(self):
        return ShopProduct.objects.filter(id__in=Product.objects.all_except_deleted()).distinct()

    def get_view_name(self):
        return _("Shop Products")

    @classmethod
    def get_help_text(cls):
        return _("Shop Products can be listed, fetched, created, updated and deleted.")


class ProductTypeViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, viewsets.ModelViewSet):
    """
    retrieve: Fetches a product type by its ID.

    list: Lists all available product types.

    delete: Deletes a product type.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new product type.

    update: Fully updates an existing product type.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product type.
    You can update only a set of attributes.
    """

    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer

    def get_view_name(self):
        return _("Product type")

    @classmethod
    def get_help_text(cls):
        return _("Product types can be listed, fetched, created, updated and deleted.")


class ProductAttributeViewSet(PermissionHelperMixin,
                              ProtectedModelViewSetMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin,
                              mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """
    retrieve: Fetches a product attribute by its ID.

    delete: Deletes a product attribute.
    If the object is related to another one and the relationship is protected, an error will be returned.

    update: Fully updates an existing product attribute.
    You must specify all parameters to make it possible to overwrite all object  attributes.

    partial_update: Updates an existing product attribute.
    You can update only a set of attributes.
    """

    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer

    def get_view_name(self):
        return _("Product Attribute")

    @classmethod
    def get_help_text(cls):
        return _("Products attributes can be fetched, updated and deleted.")


class ProductPackageViewSet(PermissionHelperMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    """
    retrieve: Fetches a product package link by its ID.

    delete: Deletes a product package link.
    If the object is related to another one and the relationship is protected, an error will be returned.

    update: Fully updates an existing product package link.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing product package link.
    You can update only a set of attributes.
    """

    queryset = ProductPackageLink.objects.all()
    serializer_class = ProductPackageLinkSerializer

    def get_view_name(self):
        return _("Product Package Link")

    @classmethod
    def get_help_text(cls):
        return _("Products package links can be fetched, updated and deleted.")
