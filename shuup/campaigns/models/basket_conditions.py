# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from polymorphic.models import PolymorphicModel

from shuup.campaigns.utils.campaigns import (
    get_product_ids_and_quantities, get_total_price_of_products
)
from shuup.campaigns.utils.time_range import is_in_time_range
from shuup.core.fields import MoneyValueField
from shuup.core.models import (
    Category, Contact, ContactGroup, Product, ShopProduct
)
from shuup.core.pricing import PricingContext
from shuup.utils.properties import MoneyPropped, PriceProperty


class BasketCondition(PolymorphicModel):
    model = None
    active = models.BooleanField(default=True)
    name = _("Basket condition")

    def matches(self, basket, lines):
        return False

    def __str__(self):
        return force_text(self.name)


class BasketTotalProductAmountCondition(BasketCondition):
    identifier = "basket_product_condition"
    name = _("Basket product count")

    product_count = models.DecimalField(
        verbose_name=_("product count in basket"), blank=True, null=True, max_digits=36, decimal_places=9)

    def matches(self, basket, lines):
        # if the campaign has a supplier, count only products from that supplier
        campaign = self.campaign.first()
        supplier = campaign.supplier if hasattr(campaign, "supplier") and campaign.supplier else None
        return (basket.count_products(supplier) >= self.product_count)

    @property
    def description(self):
        return _("Limit the campaign to match when basket has at least the product count entered here.")

    @property
    def value(self):
        return self.product_count

    @value.setter
    def value(self, value):
        self.product_count = value


class BasketTotalAmountCondition(MoneyPropped, BasketCondition):
    identifier = "basket_amount_condition"
    name = _("Basket total value")

    amount = PriceProperty("amount_value", "campaign.shop.currency", "campaign.shop.prices_include_tax")
    amount_value = MoneyValueField(default=None, blank=True, null=True, verbose_name=_("basket total amount"))

    def matches(self, basket, lines):
        campaign = self.campaign.first()
        total_of_products = get_total_price_of_products(basket, campaign)
        return (total_of_products.value >= self.amount_value)

    @property
    def description(self):
        return _("Limit the campaign to match when it has at least the total value entered here worth of products.")

    @property
    def value(self):
        return self.amount_value

    @value.setter
    def value(self, value):
        self.amount_value = value


class BasketTotalUndiscountedProductAmountCondition(MoneyPropped, BasketCondition):
    identifier = "basket_amount_condition_undiscounted"
    name = _("Undiscounted basket total value")

    amount = PriceProperty("amount_value", "campaign.shop.currency", "campaign.shop.prices_include_tax")
    amount_value = MoneyValueField(default=None, blank=True, null=True, verbose_name=_("basket total amount"))

    def matches(self, basket, lines):
        from shuup.campaigns.models import CatalogCampaign
        campaign = self.campaign.first()
        total_of_products = get_total_price_of_products(basket, campaign)
        product_lines = basket.get_product_lines()

        if hasattr(campaign, "supplier") and campaign.supplier:
            product_lines = [line for line in product_lines if line.supplier == campaign.supplier]

        total_undiscounted_price_value = total_of_products.value
        shop = basket.shop
        context = PricingContext(shop, basket.customer)

        for line in product_lines:
            if CatalogCampaign.get_matching(context, line.product.get_shop_instance(shop)):
                total_undiscounted_price_value -= line.price.value
        return (total_undiscounted_price_value >= self.amount_value)

    @property
    def description(self):
        return _("Limit the campaign to match when it has at least the total value "
                 "entered here worth of products which doesn't have already discounts.")

    @property
    def value(self):
        return self.amount_value

    @value.setter
    def value(self, value):
        self.amount_value = value


class BasketMaxTotalProductAmountCondition(BasketCondition):
    identifier = "basket_max_product_condition"
    name = _("Basket maximum product count")

    product_count = models.DecimalField(
        verbose_name=_("maximum product count in basket"), blank=True, null=True, max_digits=36, decimal_places=9)

    def matches(self, basket, lines):
        campaign = self.campaign.first()
        supplier = campaign.supplier if hasattr(campaign, "supplier") and campaign.supplier else None
        return (basket.count_products(supplier) <= self.product_count)

    @property
    def description(self):
        return _("Limit the campaign to match when basket has at maximum the product count entered here.")

    @property
    def value(self):
        return self.product_count

    @value.setter
    def value(self, value):
        self.product_count = value


class BasketMaxTotalAmountCondition(MoneyPropped, BasketCondition):
    identifier = "basket_max_amount_condition"
    name = _("Basket maximum total value")

    amount = PriceProperty("amount_value", "campaign.shop.currency", "campaign.shop.prices_include_tax")
    amount_value = MoneyValueField(default=None, blank=True, null=True, verbose_name=_("maximum basket total amount"))

    def matches(self, basket, lines):
        campaign = self.campaign.first()
        total_of_products = get_total_price_of_products(basket, campaign)
        return (total_of_products.value <= self.amount_value)

    @property
    def description(self):
        return _("Limit the campaign to match when it has at maximum the total value entered here worth of products.")

    @property
    def value(self):
        return self.amount_value

    @value.setter
    def value(self, value):
        self.amount_value = value


class ComparisonOperator(Enum):
    EQUALS = 0
    GTE = 1

    class Labels:
        EQUALS = _('Exactly')
        GTE = _('Greater than or equal to')


class ProductsInBasketCondition(BasketCondition):
    identifier = "basket_products_condition"
    name = _("Products in basket")

    model = Product

    operator = EnumIntegerField(
        ComparisonOperator, default=ComparisonOperator.GTE, verbose_name=_("operator"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantity"))
    products = models.ManyToManyField(Product, verbose_name=_("products"), blank=True)

    def matches(self, basket, lines):
        campaign = self.campaign.first()
        supplier = campaign.supplier if hasattr(campaign, "supplier") and campaign.supplier else None
        product_id_to_qty = get_product_ids_and_quantities(basket, supplier)
        product_ids = self.products.filter(id__in=product_id_to_qty.keys()).values_list("id", flat=True)
        for product_id in product_ids:
            if self.operator == ComparisonOperator.GTE:
                return product_id_to_qty[product_id] >= self.quantity
            elif self.operator == ComparisonOperator.EQUALS:
                return product_id_to_qty[product_id] == self.quantity
        return False

    @property
    def description(self):
        return _("Limit the campaign to have the selected products in basket.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, value):
        self.products = value


class ContactGroupBasketCondition(BasketCondition):
    model = ContactGroup
    identifier = "basket_contact_group_condition"
    name = _("Contact Group")

    contact_groups = models.ManyToManyField(ContactGroup, verbose_name=_("contact groups"))

    def matches(self, basket, lines=[]):
        contact_group_ids = basket.customer.groups.values_list("pk", flat=True)
        return self.contact_groups.filter(pk__in=contact_group_ids).exists()

    @property
    def description(self):
        return _("Limit the campaign to members of the selected contact groups.")

    @property
    def values(self):
        return self.contact_groups

    @values.setter
    def values(self, values):
        self.contact_groups = values


class ContactBasketCondition(BasketCondition):
    model = Contact
    identifier = "basket_contact_condition"
    name = _("Contact")

    contacts = models.ManyToManyField(Contact, verbose_name=_("contacts"))

    def matches(self, basket, lines=[]):
        customer = basket.customer
        return bool(customer and self.contacts.filter(pk=customer.pk).exists())

    @property
    def description(self):
        return _("Limit the campaign to selected contacts.")

    @property
    def values(self):
        return self.contacts

    @values.setter
    def values(self, values):
        self.contacts = values


class CategoryProductsBasketCondition(BasketCondition):
    model = Category
    identifier = "basket_category_condition"
    name = _("Category products in basket")

    operator = EnumIntegerField(
        ComparisonOperator, default=ComparisonOperator.GTE, verbose_name=_("operator"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantity"))
    categories = models.ManyToManyField(Category, related_name="+", verbose_name=_("categories"))
    excluded_categories = models.ManyToManyField(
        Category, blank=True, related_name="+", verbose_name=_("excluded categories"),
        help_text=_(
            "If the customer has even a single product in the basket from these categories "
            "this rule won't match thus the campaign cannot be applied to the basket."
        ))

    def matches(self, basket, lines):
        product_id_to_qty = get_product_ids_and_quantities(basket)
        if ShopProduct.objects.filter(
                product_id__in=product_id_to_qty.keys(), categories__in=self.excluded_categories.all()).exists():
            return False

        product_ids = ShopProduct.objects.filter(
            categories__in=self.categories.all(), product_id__in=product_id_to_qty.keys()
        ).values_list("product_id", flat=True)
        product_count = sum(product_id_to_qty[product_id] for product_id in product_ids)
        if self.operator == ComparisonOperator.EQUALS:
            return bool(product_count == self.quantity)
        else:
            return bool(product_count >= self.quantity)

    @property
    def description(self):
        return _("Limit the campaign to match the products from selected categories.")


class HourBasketCondition(BasketCondition):
    identifier = "hour_condition"
    name = _("Day and hour")

    hour_start = models.TimeField(
        verbose_name=_("start time"),
        help_text=_("12pm is considered noon and 12am as midnight.")
    )
    hour_end = models.TimeField(
        verbose_name=_("end time"),
        help_text=_("12pm is considered noon and 12am as midnight. End time is not considered match.")
    )
    days = models.CharField(max_length=255, verbose_name=_("days"))

    def matches(self, basket, lines):
        return is_in_time_range(timezone.now(), self.hour_start, self.hour_end, self.values)

    @property
    def description(self):
        return _("Limit the campaign to selected days.")

    @property
    def values(self):
        return [v for v in map(int, self.days.split(","))]
