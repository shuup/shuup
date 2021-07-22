Product Catalog API
===================

This is the API that is used to list available products from the database.

It has methods to return a queryset of products or shop products with prices annotated.

The product catalog object receives a context parameter in the object constructor in
order to configure the product filtering:

.. code:: python

    # configure a context for a shop and only pull purchasable products
    catalog_context = ProductCatalogContext(shop=my_shop, purchasable_only=False)

    # create the catalog instance with the configured context
    catalog = ProductCatalog(context=catalog_context)

    # iterate over all the products and print their price (for the given context)
    for product in catalog.get_products_queryset():
        print(product.catalog_price)

The Catalog API was built to be a layer on top of all the custom product pricing module to simplify and make the access to the prices performant in huge catalogs.

The Catalog API should be used while listing products, rendering them on a list of even using it on a REST API.

To access the products prices in a quick way, they are indexed in the ``ProductCatalogPrice`` model. Every time a product is saved in the admin, a signal (``on_object_saved``) is triggered and the ``ProductCatalog`` will index the changed product.

The ``ProductCatalog`` will call the pricing module to index prices for the given shop product and after that it will trigger a the signal ``index_catalog_shop_product`` which can be then handled by other apps to handle other tasks like cache bumping.

The indexed prices contain a shop and can contain a specific supplier, a specific contact group and a specific contact.

The discounted price will also index as the discounted price as the ``ProductCatalog`` will call every discount module to index the product.

It's the responsibility of the supplier modules to listen to the ``index_catalog_shop_product`` signal and index the availability of the product, updating the ``ProductCatalogPrice`` model instance accordingly. If the supplier module don't do that, the product won't be marked as available (purchasable) and it won't be visible in listing when the ``ProductCatalogContext`` is configured to have ``purchasable_only`` flag set to ``True``.

