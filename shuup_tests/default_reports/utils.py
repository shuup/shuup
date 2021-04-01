# -*- coding: utf-8 -*-
import random

from shuup.core.models import Product
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    create_random_person,
    get_default_shop,
    get_default_supplier,
)


def create_orders_for_dates(dates, as_paid=False):
    shop = get_default_shop()
    supplier = get_default_supplier()
    customer = create_random_person()
    products = []

    def get_sku():
        return "test-%s" % random.randint(10000, 999999)

    for i in range(20):
        sku = get_sku()
        price = random.randint(1, 11) * 5
        if Product.objects.filter(sku=sku).exists():
            sku = get_sku()
        product = create_product(sku, shop, supplier, price)
        products.append(product)

    orders = []
    for date in dates:
        product = random.choice(products)
        sp = product.get_shop_instance(shop)

        quantity = random.randint(0, 10)
        order = create_order_with_product(product, supplier, quantity, sp.default_price, shop=shop)
        order.order_date = date
        order.customer = customer
        order.save()

        if as_paid:
            order.create_payment(order.taxful_total_price)

        orders.append(order)

    return {
        "created_products": products,
        "created_orders": orders,
        "shop": shop,
        "customer": customer,
        "orders": orders,
    }
