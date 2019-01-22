Performance & Optimizations
===========================

This part of the documentation explains how to keep the best performance in Shuup by paying attention to how Shuup works internally.

Below there are some essential concepts that need to be clarified to understand how pieces work together internally.

Visibility, purchasability and orderability
--------------------------------------------

These concepts help you to understand how Shuup deal with different product states.

Visibility
^^^^^^^^^^

A product can be invisible for a customer, for a group of customers, for logged in users, for everyone or just hidden.

Visibility is configurable through product admin using visibility options. Deleted products are always invisible as internally it just set a deleted flag.

Visibility is the base layer of filtering which is applied when listing products in the storefront. You can use ``Product.objects.listed`` and ``Product.objects.searchabale`` to list your products to the storefront.

Purchasability
^^^^^^^^^^^^^^

The customer can purchase product only when there is stock for it and all possible child products when the product is a variation parent or a package. Besides that, a product can have a set of rules to be able to be purchased as a minimum purchase quantity and multiple quantities.

The customer can purchase the product when it matches all these criteria. The product also has a purchasable flag in cases the merchant wants to disable the purchasability of the product but still wants to make it visible at the storefront.

Orderability
^^^^^^^^^^^^

The orderability of a product is the combination of visibility and purchasability. Users can only order products which are visible and match all the purchasability criteria mentioned before.

Listing products at the storefront
----------------------------------

By default, Shuup lists all visible products at the storefront, even not purchasable products are listed. Listing visible products is in most cases most performant behavior since the purchasability checks are expensive to be done and can not be achieved through a simple database join or Django queryset, like the visibility check.

Purchasable checks are expensive because of the potential complexity of supplier orderability check. For example, supplier module can use some real-time service to check stock counts or orderability.

By default, orderability should be done only in places where it is vital, like the product detail page, basket, and checkout.

In case you don't want to show unorderable products then you should likely hide the products when they become unorderable. To add custom logic for product orderability and visibility you can add a receiver for ``shuup.core.signals.stocks_udpated`` . For custom visibility receiver see ``shuup.testing.receivers.shop_product_orderability_check``.

Listing products using plugins
------------------------------

Shuup contains some Xtheme plugins to render highlighted product, category products, discounted products and cross sales products. All of the product plugins have the configuration of how many products to be returned and whether only orderable products should be rendered.

When the orderability flag is enabled, Shuup fetches the desired number of visible products from the database and after that apply all possible filters for the products fetched. Filtering products after the fetch means that if all products returned from the database are unorderable, the plugin does not render anything.

Filtering products after the product fetch avoids looping over all visible products of the database until we reach the number of desired products. To ensure exact amount of products defined by the plugin when the orderability filter is on the merchant should hide unorderable products that could be shown by the highlight plugin.
