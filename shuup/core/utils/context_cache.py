# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from parler.managers import TranslatableQuerySet

from shuup.core import cache

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:  # Py2 fallback
    from urlparse import urlparse, parse_qs

HASHABLE_KEYS = ["customer_groups", "customer", "shop"]

GENERIC_CACHE_NAMESPACE_PREFIX = "generic_context_cache"


def get_cached_value(identifier, item, context, **kwargs):
    """
    Get item from context cache by identifier

    Accepts optional kwargs parameter `allow_cache` which will skip
    fetching the actual cached object. When `allow_cache` is set to
    False only cache key for identifier, item, context combination is
    returned.

    :param identifier: Any
    :type identifier: string
    :param item: Any
    :param context: Any
    :type context: dict
    :return: Cache key and cached value if allowed
    :rtype: tuple(str, object)
    """
    allow_cache = True
    if "allow_cache" in kwargs:
        allow_cache = kwargs.pop("allow_cache")
    key = get_cache_key_for_context(identifier, item, context, **kwargs)
    if not allow_cache:
        return key, None
    return key, cache.get(key)


def set_cached_value(key, value, timeout=None):
    """
    Set value to context cache

    :param key: Unique key formed to the context
    :param value: Value to cache
    :param timeout: Timeout as seconds
    :type timeout: int
    """
    cache.set(key, value, timeout=timeout)


def bump_cache_for_shop_product(instance, shop=None):
    """
    Bump cache for given shop product

    Clear cache for shop product, product linked to it and
    all the children.

    :param shop_product: shop product object or shop product object id
    :type shop_product: shuup.core.models.ShopProduct
    """
    from shuup.core.models import ShopProduct, ProductPackageLink, Product

    if isinstance(instance, ShopProduct):
        shop_product_ids = [instance.pk]
    elif isinstance(instance, QuerySet):
        shop_product_ids = instance
    else:
        shop_product_ids = [instance]

    # Get all normal products linked to passed
    # shop product id
    product_ids = Product.objects.filter(
        shop_products__id__in=shop_product_ids
    ).values_list("id", flat=True)

    # Get all affect variation parent ids just in
    # case passed shop product ids includes child
    # products we need to bump simplings
    variation_parent_ids = Product.objects.filter(
        id__in=product_ids
    ).values_list("variation_parent_id", flat=True)

    # Get all packages or products in any package
    package_product_ids = ProductPackageLink.objects.filter(
        Q(parent_id__in=product_ids) | Q(child_id__in=product_ids)
    ).values_list("child_id", "parent_id")

    # All above querysets should in theory be lazy and executed once
    # here
    product_ids_to_bump = Product.objects.filter(
        Q(id__in=product_ids) |
        Q(variation_parent_id__in=product_ids) |
        Q(variation_parent_id__in=variation_parent_ids) |
        Q(id__in=set(value for pair_of_values in package_product_ids for value in pair_of_values)
          )).values_list("id", flat=True)

    # One extra query should be better what we have now
    shop_product_ids_to_bump = ShopProduct.objects.filter(
        product_id__in=product_ids_to_bump
    ).values_list("id", flat=True)

    bump_cache_for_item_ids(shop_product_ids_to_bump, "shuup-shopproduct", ShopProduct, shop)
    bump_cache_for_item_ids(product_ids_to_bump, "shuup-product", Product, shop)


def bump_cache_for_product(product, shop=None):
    """
    Bump cache for product

    In case shop is not given all the shop products
    for the product is bumped.

    :param product: product object or product object id or a list of product object id's
    :type product: shuup.core.models.Product
    :param shop: shop object
    :type shop: shuup.core.models.Shop|None
    """
    from shuup.core.models import ShopProduct

    if not isinstance(product, list):
        product_id = (product.id if hasattr(product, "id") else product)
        products = [product_id]
    else:
        products = product

    shop_product_ids = ShopProduct.objects.filter(product_id__in=products).values_list("pk", flat=True)
    for shop_product_id in shop_product_ids:
        bump_cache_for_shop_product(shop_product_id, shop)


def bump_cache_for_item_ids(item_ids, namespace, object_class, shop=None):
    """
    Bump cache for given item ids

    Use this only for non product items. For products
    and shop_products use `bump_cache_for_product` and
    `bump_cache_for_shop_product` for those.

    `shop` parameter is deprecated and not used

    :param ids: list of cached object id's
    """
    for item_id in item_ids:
        cache.bump_version("{}-{}".format(namespace, item_id))


def bump_cache_for_item(item):
    """
    Bump cache for given item

    Use this only for non product items. For products
    and shop_products use `bump_cache_for_product` and
    `bump_cache_for_shop_product` for those.

    :param item: Cached object
    """
    cache.bump_version(_get_namespace_for_item(item))


def bump_cache_for_pk(cls, pk):
    """
    Bump cache for given class and pk combination

    Use this only for non product items. For products
    and shop_products use `bump_cache_for_product` and
    `bump_cache_for_shop_product` for those.

    In case you need to use this to product or shop_product
    make sure you also bump related objects like in
    `bump_cache_for_shop_product`.

    :param cls: Class for cached object
    :param pk: pk for cached object
    """
    cache.bump_version("%s-%s" % (_get_namespace_prefix(cls), pk))


def bump_product_signal_handler(sender, instance, **kwargs):
    """
    Signal handler for clearing product cache

    :param instance: Shuup product
    :type instance: shuup.core.models.Product
    """
    bump_cache_for_product(instance)


def bump_shop_product_signal_handler(sender, instance, **kwargs):
    """
    Signal handler for clearing shop product cache

    :param instance: Shuup shop product
    :type instance: shuup.core.models.ShopProduct
    """
    bump_cache_for_shop_product(instance)


def get_cache_key_for_context(identifier, item, context, **kwargs):
    namespace = _get_namespace_for_item(item)

    items = _get_items_from_context(context)

    for k, v in six.iteritems(kwargs):
        items[k] = _get_val(v)

    if isinstance(context, WSGIRequest):
        query_string = urlparse(context.get_full_path()).query
        for k, v in six.iteritems(parse_qs(query_string)):
            items[k] = _get_val(v)

    return "%s:%s_%s" % (namespace, identifier, hash(frozenset(items.items())))


def bump_internal_cache():
    cache.bump_version("_ctx_cache")


def _get_cached_value_from_context(context, key, value):
    cached_value = None

    # 1) check whether the value is cached inside the context as an attribute
    try:
        cache_key = "_ctx_cache_{}".format(key)
        cached_value = getattr(context, cache_key)
    except AttributeError:
        pass

    # 2) Check whether the value is cached in general cache
    # we can only cache objects that has `pk` attribute
    if cached_value is None and hasattr(value, "pk"):
        cache_key = "_ctx_cache:{}_{}".format(key, value.pk)
        cached_value = cache.get(cache_key)

    # 3) Nothing is cached, then read the value itself
    if cached_value is None:
        if key == "customer" and value:
            cached_value = _get_val(value.groups.all())
        else:
            cached_value = _get_val(value)

        # Set the value as attribute of the context
        # somethings this will raise AttributeError because the
        # context is not a valid object, like a dictionary
        try:
            cache_key = "_ctx_cache_{}".format(key)
            setattr(context, cache_key, cached_value)
        except AttributeError:
            pass

        # cache the value in the general cache
        if hasattr(value, "pk"):
            cache_key = "_ctx_cache:{}_{}".format(key, value.pk)
            cache.set(cache_key, cached_value)

    return cached_value


def _get_items_from_context(context):   # noqa (C901)
    items = {}

    def handle_item(context, key, value):
        value = _get_cached_value_from_context(context, key, value)
        if key == "customer":
            key = "customer_groups"
        items[key] = value

    if hasattr(context, "items"):
        for key, value in list(six.iteritems(context)):
            if key in HASHABLE_KEYS:
                handle_item(context, key, value)
    else:
        for key in HASHABLE_KEYS:
            if hasattr(context, key):
                value = getattr(context, key, None)
                handle_item(context, key, value)

    return items


def _get_val(v):
    if isinstance(v, dict):
        return hash(frozenset(v.items()))
    if hasattr(v, "pk"):
        return v.pk
    if isinstance(v, QuerySet) or isinstance(v, TranslatableQuerySet):
        return "|".join(list(map(str, v.all().values_list("pk", flat=True))))
    if isinstance(v, list):
        return "|".join(list(map(str, v)))
    return v


def _get_namespace_for_item(item):
    return "%s-%s" % (_get_namespace_prefix(item), _get_item_id(item))


def _get_namespace_prefix(item):
    if hasattr(item, "_meta"):
        model_meta = item._meta
        return "%s-%s" % (model_meta.app_label, model_meta.model_name)
    return GENERIC_CACHE_NAMESPACE_PREFIX


def _get_item_id(item):
    if isinstance(item, int):
        return item

    item_id = 0
    if item:
        if isinstance(item, six.string_types):
            item_id = item
        elif hasattr(item, "pk"):
            item_id = item.pk or 0
        else:
            item_id = item.__class__.lower() if callable(item) else 0
    return item_id
