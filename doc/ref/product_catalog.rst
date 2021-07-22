Product Catalog API
===================

This is the API that is used to list available products from the database.

It has methods to return a queryset of products or shop products with prices annotated.

The product catalog object receives a context parameter in the object constructor in order to configure the product filtering:

.. code:: python

    # configure a context for a shop and only pull purchasable products
    catalog_context = ProductCatalogContext(shop=my_shop, purchasable_only=False)

    # create the catalog instance with the configured context
    catalog = ProductCatalog(context=catalog_context)

    # iterate over all the products and print their price (for the given context)
    for product in catalog.get_products_queryset():
        print(product.catalog_price)

The Catalog API was built to be a layer on top of all the custom product pricing module to simplify and make the access to the prices performant in huge catalogs.

The Catalog API should always be used while rendering products on a template or returning them through a REST API, as it is possible to filter, sort and paginate the queryset easily.

To access the products prices in a quick way, they are indexed in the ``ProductCatalogPrice`` model. Every time a product is saved in the admin, a signal (``on_object_saved``) is triggered and the ``ProductCatalog`` will index the changed product.

The ``ProductCatalog`` will call the current pricing module to index prices for the given shop product and after that it will trigger the signal ``index_catalog_shop_product`` which can be then handled by other apps to execute other procedures like bumping caches.

The indexed prices contain a shop, a supplier and optionally a price rule. The price rule is basically a context when the price should be available, e.g., when a specific contact group or a specific contact is doing the request.

The discounted prices will also be indexed. The ``ProductCatalog`` will call every discount module to index the product discounted price. Every discount module should index its own discounted price. The best discounted price will be used. Discounted prices also have their catalog rules, which means discounts can be indexed by contact group and/or contact.

It's the responsibility of the supplier modules to listen to the ``index_catalog_shop_product`` signal and index the availability of the product, updating the ``ProductCatalogPrice`` model instance accordingly. If the supplier modules don't do that, the product won't be marked as available (purchasable) and it won't be visible in listing when the ``ProductCatalogContext`` is configured to have ``purchasable_only`` flag set to ``True``.

As the pricing and discount index task is a heavy process, Shuup must be configured to have tasks running in a background executor, like Celery.

How prices are indexed
----------------------

After a product is saved in admin, the ``ProductCatalog`` will call the current pricing module to index the price of the changed shop product.

The index price (saved inside ``ProductCatalogPrice``) should always match the price of the product returned by the ``get_price_info()`` of the pricing module.

The pricing module is responsible by indexing all possible prices for all different contexts, which can be a different price for a specific group and/or contact.

How discounted prices are indexed
---------------------------------

After a product is saved in admin, the ``ProductCatalog`` will call all the active discount modules to index the price of the changed shop product.

The index price (saved inside ``ProductCatalogDiscountedPrice``) should always match the discounted price of the product returned by the ``discount_price()`` of the discount module.

The discount module is responsible by indexing all possible discounted prices for all different contexts, which can be a different discounted price for a specific group, contact, date range and time range.

How availability of products are indexed
----------------------------------------

After a product is saved in admin, the ``ProductCatalog`` will call all the suppliers of the shop product to update their availability. The availability is saved inside the ``ProductCatalogPrice`` model, as a product without price is also not available for purchase.

The supplier module must update the ``is_available`` flag of every existing ``ProductCatalogPrice`` instance related to the shop product.
