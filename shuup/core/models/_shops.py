# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.managers import TranslatableManager
from parler.models import TranslatedFields

from shuup.core.fields import CurrencyField, InternalIdentifierField
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.utils.analog import define_log_model
from shuup.utils.django_compat import force_text

from ._base import ChangeProtected, TranslatableShuupModel
from ._orders import Order


def _get_default_currency():
    return settings.SHUUP_HOME_CURRENCY


class ShopManager(TranslatableManager):
    def get_for_user(self, user):
        qs = self.get_queryset()
        if getattr(user, "is_superuser", False):
            return qs.all()
        return qs.filter(staff_members=user)


class ShopStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _('disabled')
        ENABLED = _('enabled')


@python_2_unicode_compatible
class Shop(ChangeProtected, TranslatableShuupModel):
    protected_fields = ["currency", "prices_include_tax"]
    change_protect_message = _("The following fields can't be changed because there are existing orders for this shop.")

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_('modified on'))
    identifier = InternalIdentifierField(unique=True, max_length=128)
    domain = models.CharField(max_length=128, blank=True, null=True, unique=True, verbose_name=_("domain"), help_text=_(
        "Your shop domain name. Use this field to configure the URL that is used to visit your store front. "
        "Note: this requires additional configuration through your internet domain registrar."
    ))
    status = EnumIntegerField(ShopStatus, default=ShopStatus.DISABLED, verbose_name=_("status"), help_text=_(
        "Your shop's status. Disable your shop if it's no longer in use. "
        "For temporary closing enable the maintenance mode, available in the `Maintenance Mode` tab on the left."
    ))
    owner = models.ForeignKey(to="Contact", blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("contact"))
    options = JSONField(blank=True, null=True, verbose_name=_("options"))
    currency = CurrencyField(default=_get_default_currency, verbose_name=_("currency"), help_text=_(
        "The primary shop currency. This is the currency used when selling the products."
    ))
    prices_include_tax = models.BooleanField(default=True, verbose_name=_("prices include tax"), help_text=_(
        "This option defines whether product prices entered in admin include taxes. "
        "Note: this behavior can be overridden with contact group pricing."
    ))
    logo = FilerImageField(
        verbose_name=_("logo"), blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_("Shop's logo. Will be shown at theme."), related_name="shop_logos")

    favicon = FilerImageField(
        verbose_name=_("favicon"), blank=True, null=True, on_delete=models.SET_NULL, help_text=_(
            "Shop's favicon - a mini-image graphically representing your shop. "
            "Depending on the browser, it will be shown next to the address bar "
            "and/or on the website title tab."
        ), related_name="shop_favicons")

    maintenance_mode = models.BooleanField(verbose_name=_("maintenance mode"), default=False, help_text=_(
        "Enable if you want to make your shop temporarily unavailable to visitors while you do "
        "regular shop maintenance, fight the security breach or for some other reason. "
        "If you don't plan to have this shop open again, "
        "change the `Status` on the main `General Information` tab to `Disabled`."
    ))
    contact_address = models.ForeignKey(
        "MutableAddress", verbose_name=_("contact address"), blank=True, null=True, on_delete=models.SET_NULL)
    staff_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="shops", verbose_name=_('staff members'))
    labels = models.ManyToManyField("Label", blank=True, related_name="shops", verbose_name=_("labels"))

    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_("name"), help_text=_(
            "The shop name. This name is displayed throughout Admin Panel."
        )),
        public_name=models.CharField(max_length=64, verbose_name=_("public name"), help_text=_(
            "The public shop name. This name is displayed in the store front and in any customer email correspondence."
        )),
        description=models.TextField(
            blank=True, verbose_name=_('description'),
            help_text=_(
                "To make your shop stand out, give it an awesome description. "
                "This is what will help your shoppers learn about your shop. "
                "It will also help shoppers find your store from the web."
            )
        ),
        short_description=models.CharField(
            max_length=150, blank=True, verbose_name=_('short description'),
            help_text=_(
                "Enter a short description for your shop. The short description will "
                "be used to get the attention of your customer with a small, but "
                "precise description of your shop. It also helps with getting more "
                "traffic via search engines."
            )
        ),
        maintenance_message=models.CharField(
            max_length=300, blank=True, verbose_name=_("maintenance message"), help_text=_(
                "The message to display to customers while your shop is in a maintenance mode."
            )
        )
    )

    objects = ShopManager()

    class Meta:
        verbose_name = _('shop')
        verbose_name_plural = _('shops')

    def __str__(self):
        return force_text(self.safe_translation_getter("name", default="Shop %d" % self.pk))

    def create_price(self, value):
        """
        Create a price with given value and settings of this shop.

        Takes the ``prices_include_tax`` and ``currency`` settings of
        this Shop into account.

        :type value: decimal.Decimal|int|str
        :rtype: shuup.core.pricing.Price
        """
        if self.prices_include_tax:
            return TaxfulPrice(value, self.currency)
        else:
            return TaxlessPrice(value, self.currency)

    def _are_changes_protected(self):
        return Order.objects.filter(shop=self).exists()


ShopLogEntry = define_log_model(Shop)
