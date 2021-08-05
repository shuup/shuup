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
