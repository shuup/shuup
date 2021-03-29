# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import django
import functools
import six
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedField, TranslatedFields
from uuid import uuid4

from shuup.core.fields import InternalIdentifierField
from shuup.core.pricing import PriceInfo

from ._base import PolymorphicShuupModel, PolymorphicTranslatableShuupModel, PolyTransModelBase, TranslatableShuupModel
from ._product_shops import ShopProduct
from ._shops import Shop


class ServiceProvider(PolymorphicTranslatableShuupModel):
    """
    Entity that provides services.

    Good examples of service providers are `Carrier` and
    `PaymentProcessor`.

    When subclassing `ServiceProvider`, set value for `service_model`
    class attribute. It should be a model class, which is a subclass of
    `Service`.
    """

    identifier = InternalIdentifierField(unique=True)
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("enabled"),
        help_text=_("Enable this if this service provider can be used when placing orders."),
    )
    name = TranslatedField(any_language=True)
    logo = FilerImageField(blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("logo"))

    base_translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_("name"), help_text=_("The service provider name.")),
    )

    shops = models.ManyToManyField(
        "shuup.Shop",
        verbose_name=_("shops"),
        related_name="service_providers",
        help_text=_(
            "This service provider will be available only for order sources of the given shop. "
            "If blank, this service provider is available for any order source."
        ),
        blank=True,
    )
    supplier = models.ForeignKey(
        "shuup.Supplier",
        on_delete=models.CASCADE,
        verbose_name=_("supplier"),
        related_name="service_providers",
        help_text=_(
            "This service provider will be available only for order sources that contain "
            "all items from the configured supplier. If blank, this service provider is "
            "available for any order source."
        ),
        blank=True,
        null=True,
    )

    #: Model class of the provided services (subclass of `Service`)
    service_model = None

    def get_service_choices(self):
        """
        Get all service choices of this provider.

        Subclasses should implement this method.

        :rtype: list[ServiceChoice]
        """
        raise NotImplementedError

    def create_service(self, choice_identifier, **kwargs):
        """
        Create a service for a given choice identifier.

        Subclass implementation may attach some `behavior components
        <ServiceBehaviorComponent>` to the created service.

        Subclasses should provide implementation for `_create_service`
        or override it. Base class implementation calls the
        `_create_service` method with resolved `choice_identifier`.

        :type choice_identifier: str|None
        :param choice_identifier:
          Identifier of the service choice to use.  If None, use the
          default service choice.
        :rtype: shuup.core.models.Service
        """
        if choice_identifier is None:
            choice_identifier = self.get_service_choices()[0].identifier
        return self._create_service(choice_identifier, **kwargs)

    def _create_service(self, choice_identifier, **kwargs):
        """
        Create a service for a given choice identifier.

        :type choice_identifier: str
        :rtype: shuup.core.models.Service
        """
        raise NotImplementedError

    def get_effective_name(self, service, source):
        """
        Get effective name of the service for a given order source.

        Base class implementation will just return name of the given
        service, but that may be changed in a subclass.

        :type service: shuup.core.models.Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: str
        """
        return service.name


class ServiceChoice(object):
    """
    Choice of service provided by a service provider.
    """

    def __init__(self, identifier, name):
        """
        Initialize service choice.

        :type identifier: str
        :param identifier:
          Internal identifier for the service.  Should be unique within
          a single `ServiceProvider`.
        :type name: str
        :param name:
          Descriptive name of the service in currently active language.
        """
        self.identifier = identifier
        self.name = name


class ServiceQuerySet(TranslatableQuerySet):
    def enabled(self):
        no_provider_filter = {
            self.model.provider_attr: None,
        }
        enabled_filter = {
            self.model.provider_attr + "__enabled": True,
            "enabled": True,
        }
        return self.exclude(**no_provider_filter).filter(**enabled_filter)

    def for_shop(self, shop):
        return self.filter(shop=shop)

    def available_ids(self, shop, products):
        """
        Retrieve common available services for shop and product IDs.

        :param shop_id: Shop ID.
        :type shop_id: int
        :param product_ids: Product IDs.
        :type product_ids: set[int]
        :return: Set of service IDs.
        :rtype: set[int]
        """
        shop_product_m2m = self.model.shop_product_m2m
        shop_product_limiter_attr = "limit_%s" % self.model.shop_product_m2m

        limiting_products_query = {"shop": shop, "product__in": products, shop_product_limiter_attr: True}
        enabled_for_shop = self.enabled().for_shop(shop)
        available_ids = set(enabled_for_shop.values_list("pk", flat=True))

        for shop_product in ShopProduct.objects.filter(**limiting_products_query):
            available_ids &= set(getattr(shop_product, shop_product_m2m).values_list("pk", flat=True))
            if not available_ids:  # Out of IDs, better just fail fast
                break

        return available_ids

    def available(self, shop, products):
        return self.filter(pk__in=self.available_ids(shop, products))


class Service(TranslatableShuupModel):
    """
    Abstract base model for services.

    Each enabled service should be linked to a service provider and
    should have a choice identifier specified in its `choice_identifier`
    field. The choice identifier should be valid for the service
    provider, i.e. it should be one of the `ServiceChoice.identifier`
    values returned by the `ServiceProvider.get_service_choices` method.
    """

    identifier = InternalIdentifierField(unique=True, verbose_name=_("identifier"))
    enabled = models.BooleanField(
        default=False,
        verbose_name=_("enabled"),
        help_text=_("Enable this if this service should be selectable on checkout."),
    )
    shop = models.ForeignKey(
        on_delete=models.CASCADE, to=Shop, verbose_name=_("shop"), help_text=_("The shop for this service.")
    )
    supplier = models.ForeignKey(
        "shuup.Supplier",
        verbose_name=_("supplier"),
        on_delete=models.CASCADE,
        help_text=_(
            "The supplier for this service. This service will be available only for order sources "
            "that contain all items from this supplier."
        ),
        null=True,
        blank=True,
    )
    choice_identifier = models.CharField(blank=True, max_length=64, verbose_name=_("choice identifier"))

    # These are for migrating old methods to new architecture
    old_module_identifier = models.CharField(max_length=64, blank=True)
    old_module_data = JSONField(blank=True, null=True)

    name = TranslatedField(any_language=True)
    description = TranslatedField()
    logo = FilerImageField(blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("logo"))
    tax_class = models.ForeignKey(
        "TaxClass",
        on_delete=models.PROTECT,
        verbose_name=_("tax class"),
        help_text=_("The tax class to use for this service. Define by searching for `Tax Classes`."),
    )

    behavior_components = models.ManyToManyField("ServiceBehaviorComponent", verbose_name=_("behavior components"))
    labels = models.ManyToManyField("Label", blank=True, verbose_name=_("labels"))

    objects = ServiceQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def provider(self):
        """
        :rtype: shuup.core.models.ServiceProvider
        """
        return getattr(self, self.provider_attr)

    def get_effective_name(self, source):
        """
        Get an effective name of the service for a given order source.

        By default, effective name is the same as name of this service,
        but if there is a service provider with a custom implementation
        for `~shuup.core.models.ServiceProvider.get_effective_name`
        method, then this can be different.

        :type source: shuup.core.order_creator.OrderSource
        :rtype: str
        """
        if not self.provider:
            return self.name
        return self.provider.get_effective_name(self, source)

    def is_available_for(self, source):
        """
        Return true if service is available for a given source.

        :type source: shuup.core.order_creator.OrderSource
        :rtype: bool
        """
        return not any(self.get_unavailability_reasons(source))

    def get_unavailability_reasons(self, source):
        """
        Get reasons of being unavailable for a given source.

        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[ValidationError]
        """
        if not self.provider or not self.provider.enabled or not self.enabled:
            yield ValidationError(_("%s is disabled.") % self, code="disabled")

        if source.shop.id != self.shop_id:
            yield ValidationError(_("%s is for different shop.") % self, code="wrong_shop")

        for component in self.behavior_components.all():
            for reason in component.get_unavailability_reasons(self, source):
                yield reason

    def get_total_cost(self, source):
        """
        Get total cost of this service for items in a given source.

        :type source: shuup.core.order_creator.OrderSource
        :rtype: PriceInfo
        """
        return _sum_costs(self.get_costs(source), source)

    def get_costs(self, source):
        """
        Get costs of this service for items in a given source.

        :type source: shuup.core.order_creator.OrderSource
        :return: description, price and tax class of the costs.
        :rtype: Iterable[ServiceCost]
        """
        for component in self.behavior_components.all():
            for cost in component.get_costs(self, source):
                yield cost

    def get_lines(self, source):
        """
        Get lines for a given source.

        Lines are created based on costs. Costs without descriptions are
        combined to a single line.

        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[shuup.core.order_creator.SourceLine]
        """
        for (num, line_data) in enumerate(self._get_line_data(source), 1):
            (price_info, tax_class, text) = line_data
            yield self._create_line(source, num, price_info, tax_class, text)

    def _get_line_data(self, source):
        # Split to costs with and without description
        costs_with_description = []
        costs_without_description = []
        for cost in self.get_costs(source):
            if cost.description:
                costs_with_description.append(cost)
            else:
                assert cost.tax_class is None
                costs_without_description.append(cost)

        if not (costs_with_description or costs_without_description):
            costs_without_description = [ServiceCost(source.create_price(0))]

        effective_name = self.get_effective_name(source)

        # Yield the combined cost first
        if costs_without_description:
            combined_price_info = _sum_costs(costs_without_description, source)
            yield (combined_price_info, self.tax_class, effective_name)

        # Then the costs with description, one line for each cost
        for cost in costs_with_description:
            tax_class = cost.tax_class or self.tax_class
            text = _("%(service_name)s: %(sub_item)s") % {
                "service_name": effective_name,
                "sub_item": cost.description,
            }
            yield (cost.price_info, tax_class, text)

    def _create_line(self, source, num, price_info, tax_class, text):
        return source.create_line(
            line_id=self._generate_line_id(num),
            type=self.line_type,
            quantity=price_info.quantity,
            text=text,
            base_unit_price=price_info.base_unit_price,
            discount_amount=price_info.discount_amount,
            tax_class=tax_class,
            supplier=self.supplier,
            shop=self.shop,
        )

    def _generate_line_id(self, num):
        return "%s-%02d-%s" % (self.line_type.name.lower(), num, uuid4().hex)

    def _make_sure_is_usable(self):
        if not self.provider:
            raise ValueError("Error! %r has no %s." % (self, self.provider_attr))
        if not self.enabled:
            raise ValueError("Error! %r is disabled." % (self,))
        if not self.provider.enabled:
            raise ValueError("Error! %s of %r is disabled." % (self.provider_attr, self))


def _sum_costs(costs, source):
    """
    Sum the price info of given costs and return the sum as `PriceInfo`.

    :type costs: Iterable[ServiceCost]
    :type source: shuup.core.order_creator.OrderSource
    :rtype: PriceInfo
    """

    def plus(pi1, pi2):
        assert pi1.quantity == pi2.quantity
        return PriceInfo(
            pi1.price + pi2.price,
            pi1.base_price + pi2.base_price,
            quantity=pi1.quantity,
        )

    zero_price = source.create_price(0)
    zero_pi = PriceInfo(zero_price, zero_price, quantity=1)
    return functools.reduce(plus, (x.price_info for x in costs), zero_pi)


class ServiceCost(object):
    """
    A cost of a service.

    One service might have several costs.
    """

    def __init__(self, price, description=None, tax_class=None, base_price=None):
        """
        Initialize cost from values.

        Note: If `tax_class` is specified, `description` must also be given.

        :type price: shuup.core.pricing.Price
        :type description: str|None
        :type tax_class: shuup.core.models.TaxClass|None
        :type base_price: shuup.core.pricing.Price|None
        """
        if tax_class and not description:
            raise ValueError("Error! Service cost with a defined tax class must also have a description.")
        self.price = price
        self.description = description
        self.tax_class = tax_class
        self.base_price = base_price if base_price is not None else price

    @property
    def price_info(self):
        return PriceInfo(self.price, self.base_price, quantity=1)


class ServiceBehaviorComponent(PolymorphicShuupModel):
    #: Name for the component (lazy translated)
    name = None

    #: Help text for the component (lazy translated)
    help_text = None

    identifier = InternalIdentifierField(unique=True)

    def __init__(self, *args, **kwargs):
        if type(self) != ServiceBehaviorComponent and self.name is None:
            raise TypeError("Error! %s.name is not defined." % type(self).__name__)
        super(ServiceBehaviorComponent, self).__init__(*args, **kwargs)

    def get_unavailability_reasons(self, service, source):
        """
        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[ValidationError]
        """
        return ()

    def get_costs(self, service, source):
        """
        Return costs for this object. This should be implemented
        in a subclass. This method is used to calculate price for
        ``ShippingMethod`` and ``PaymentMethod`` objects.

        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[ServiceCost]
        """
        return ()

    def get_delivery_time(self, service, source):
        """
        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: shuup.utils.dates.DurationRange|None
        """
        return None


_translatable_model = PolymorphicTranslatableShuupModel if django.VERSION >= (1, 11) else TranslatableShuupModel


class TranslatableServiceBehaviorComponent(
    six.with_metaclass(PolyTransModelBase, ServiceBehaviorComponent, _translatable_model)
):
    class Meta:
        abstract = True
