# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.transaction import atomic
from six import print_

from shuup import configuration
from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.models import (
    Currency, CustomerTaxGroup, ProductType, SalesUnit, Shop, ShopStatus,
    Supplier
)
from shuup.core.telemetry import get_installation_key, is_telemetry_enabled
from shuup.xtheme import set_current_theme


def schema(model, identifier, **info):
    return locals()


class Initializer(object):
    schemata = [
        schema(
            Shop, "default", name="Default Shop", public_name="Default Shop", domain="localhost",
            status=ShopStatus.ENABLED, maintenance_mode=False),
        schema(ProductType, "default", name="Standard Product"),
        schema(ProductType, "digital", name="Digital Product"),
        schema(Supplier, "default", name="Default Supplier"),
        schema(SalesUnit, "pcs", name="Pieces", symbol="pcs"),
        schema(CustomerTaxGroup, "default_person_customers", name="Retail Customers"),
        schema(CustomerTaxGroup, "default_company_customers", name="Company Customers"),
        schema(Currency, "USD", decimal_places=2),
        schema(Currency, "EUR", decimal_places=2),
        schema(Currency, "BRL", decimal_places=2),
        schema(Currency, "JPY", decimal_places=0),
        schema(Currency, "CNY", decimal_places=2),
        schema(Currency, "GBP", decimal_places=2),
        schema(Currency, "CAD", decimal_places=2),
    ]

    def __init__(self):
        self.objects = {}

    def process_schema(self, schema):
        model = schema["model"]
        assert issubclass(model, Model)
        identifier_attr = getattr(model, "identifier_attr", "identifier")
        obj = model.objects.filter(**{identifier_attr: schema["identifier"]}).first()
        if obj:
            return obj
        print_("Creating %s..." % model._meta.verbose_name, end=" ")
        obj = model()
        setattr(obj, identifier_attr, schema["identifier"])
        for key, value in schema["info"].items():
            if value in self.objects:
                value = self.objects[value]
            setattr(obj, key, value)
        obj.full_clean()
        obj.save()
        print_(obj)
        if isinstance(obj, Supplier):
            print_("Adding shop for supplier...")
            obj.shops.add(Shop.objects.first())

        return obj

    def run(self):
        for schema in self.schemata:
            self.objects[schema["model"]] = self.process_schema(schema)

        # Ensure default statuses are available
        print_("Creating order statuses...", end=" ")
        create_default_order_statuses()
        print_("done.")
        if not settings.DEBUG and is_telemetry_enabled():
            try:
                data = json.dumps({
                    "key": get_installation_key()
                })
                resp = requests.get(url=settings.SHUUP_SUPPORT_ID_URL, data=data, timeout=5)
                if resp.json().get("support_id"):
                    configuration.set(None, "shuup_support_id", resp.json().get("support_id"))
            except Exception:
                print_("Failed to get support id.")

        set_current_theme("shuup.themes.classic_gray", Shop.objects.first())

        print_("Initialization done.")


class Command(BaseCommand):
    leave_locale_alone = True

    def handle(self, *args, **options):
        with atomic():
            Initializer().run()
