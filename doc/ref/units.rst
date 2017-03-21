Product Units in Shuup
======================

Commonly web shops sell products which are prepackaged units and their
quantities are measured in pieces.  However it is sometimes needed to be
able to sell products in non-integral quantities, like kilograms or
ounces.  In Shuup, this can be handled with sales units and display
units.

Each product in Shuup has a sales unit which determines how quantities
of the product are represented and if non-integral quantities are
allowed.  However it is possible that the sales unit has an attached
display unit which overrides the representation part.  This allows, for
example, the internal quantities to be stored in kilograms but be
displayed as grams to the customer.

``Product.sales_unit``
    Sales unit of a `~shuup.core.models.Product`.  Usually a
    `~shuup.core.models.SalesUnit` object, but can also be ``None``.
    This is the internal unit which is used to *store* the quantities,
    like quantities in the order lines or stock amounts.  Quantities
    shown to the customer should not use the sales unit, but rather a
    *display unit*, see ShopProduct.display_unit_ and or
    SalesUnit.display_unit_.

``SalesUnit.name``
    Name of `~shuup.core.models.SalesUnit`.  Usually shown only in Admin
    when managing units or when selecting sales unit for a product.

``SalesUnit.symbol``
    Symbol used when rendering values of the sales unit.

``SalesUnit.decimals``
    Number of decimals to use for values in this unit.

.. _SalesUnit.display_unit:

``SalesUnit.display_unit``
    The default display unit of the sales unit.  This property returns a
    `~shuup.core.models.DisplayUnit` object, which has the sales unit as
    its internal unit and is marked as a default, or if there is no
    default display unit for the sales unit, then this will return a
    proxy object.  The proxy object has the same display unit interface
    and mirrors the properties of the sales unit, such as symbol and
    decimals.

.. _ShopProduct.display_unit:

``ShopProduct.display_unit``
    Display unit of a shop product, a `~shuup.core.models.DisplayUnit`
    object or ``None``.

``ShopProduct.unit``
    The unit of the shop product as `~shuup.core.models.UnitInterface`.

``ShopProduct.display_quantity_step``
    Quantity step of the shop product in the display unit.

``ShopProduct..display_quantity_minimum``
    Quantity minimum of the shop product in the display unit.

``DisplayUnit.name``
    Name of the display unit.

``DisplayUnit.symbol``
    Symbol of the display unit, used when rendering quantity values in
    the display unit.

``DisplayUnit.internal_unit``
    The `~shuup.core.models.SalesUnit` object which acts as the internal
    unit for the display unit.

``DisplayUnit.ratio``
    Ratio between the display unit and its internal unit.  E.g. if
    internal unit is a kilogram and display unit is gram, then this
    should be 0.001.

``DisplayUnit.decimals``
    Number of decimals to use when representing quantity values in the
    display unit.

``DisplayUnit.comparison_value``
    Value to use for comparison purposes.  E.g. if the display unit is a
    gram with symbol "g" and this is 100, then the unit prices should be
    rendered as "$5.95 per 100g".

``DisplayUnit.allow_bare_number``
    If this boolean is true, then values of this unit can be shown
    without the symbol occasionally.  Usually wanted if the unit is a
    Piece, i.e. showing just "$5,95" in product listings rather than
    "$5,95 per pc.".

``DisplayUnit.default``
    Use this display unit as the default display unit for its internal
    unit.  If there is several default display units for an internal
    unit, then its undetermined which will be used.

``UnitInterface``
    Interface for unit related information and functionality.  Bound to
    a single display unit and its internal unit.  Can be used for
    rendering and converting product quantities in the display unit or
    in the internal unit.  Or for accessing data of either unit.  See
    the API documentation of the `~shuup.core.models.UnitInterface` for
    details.
