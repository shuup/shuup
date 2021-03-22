# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import connection

APP_LABELS = [
    "shoop_addons",
    "shoop_admin",
    "shoop_api",
    "shoop",
    "shoop_customer_group_pricing",
    "default_tax",
    "shoop_front",
    "shoop_front.auth",
    "shoop_front.customer_information",
    "shoop_front.personal_order_history",
    "shoop_front.registration",
    "shoop_front.simple_order_notification",
    "shoop_front.simple_search",
    "shoop_notify",
    "shoop_order_printouts",
    "shoop_simple_cms",
    "simple_supplier",
    "shoop_testing",
    "shoop.themes.classic_gray",
    "shoop_utils",
    "shoop_xtheme",
    "shoop_tests_core",
]

TABLES = [
    "shoop_customertaxgroup",
    "shoop_manufacturer",
    "shoop_producttype",
    "shoop_producttype_attributes",
    "shoop_salesunit",
    "shoop_shopproduct_categories",
    "shoop_shopproduct_payment_methods",
    "shoop_shopproduct_shipping_methods",
    "shoop_taxclass",
    "shoop_shopproduct_visibility_groups",
    "shoop_contactgroup_members",
    "shoop_category_visibility_groups",
    "shoop_taxclass_translation",
    "shoop_productvariationvariablevalue_translation",
    "shoop_productvariationvariable_translation",
    "shoop_producttype_translation",
    "shoop_product_translation",
    "shoop_productmedia_translation",
    "shoop_customertaxgroup_translation",
    "shoop_contactgroup_translation",
    "shoop_category_translation",
    "shoop_orderlinetax",
    "shoop_tax",
    "shoop_tax_translation",
    "shoop_category",
    "shoop_attribute",
    "shoop_attribute_translation",
    "shoop_category_shops",
    "shoop_categorylogentry",
    "shoop_companycontact_members",
    "shoop_companycontact",
    "shoop_configurationitem",
    "shoop_counter",
    "shoop_immutableaddress",
    "shoop_mutableaddress",
    "shoop_orderline",
    "shoop_orderlogentry",
    "shoop_orderstatus",
    "shoop_orderstatus_translation",
    "shoop_payment",
    "shoop_persistentcacheentry",
    "shoop_product",
    "shoop_productattribute",
    "shoop_productattribute_translation",
    "shoop_productcrosssell",
    "shoop_productlogentry",
    "shoop_productmedia",
    "shoop_productmedia_shops",
    "shoop_productpackagelink",
    "shoop_productvariationresult",
    "shoop_productvariationvariable",
    "shoop_productvariationvariablevalue",
    "shoop_salesunit_translation",
    "shoop_savedaddress",
    "shoop_shipmentproduct",
    "shoop_shopproduct_suppliers",
    "shoop_shop_translation",
    "shoop_suppliedproduct",
    "shoop_supplier",
    "shoop_front_storedbasket_products",
    "shoop_front_storedbasket",
    "shoop_notify_notification",
    "shoop_notify_script",
    "shoop_simple_cms_page_translation",
    "shoop_xtheme_savedviewconfig",
    "shoop_xtheme_themesettings",
    "shoop_shopproduct",
    "shoop_shop",
    "shoop_customer_group_pricing_cgpprice",
    "shoop_contactgroup",
    "shoop_simple_cms_page",
    "shoop_personcontact",
    "shoop_paymentmethod_translation",
    "shoop_shippingmethod_translation",
    "shoop_carrier",
    "shoop_fixedcostbehaviorcomponent",
    "shoop_paymentprocessor",
    "shoop_waivingcostbehaviorcomponent",
    "shoop_weightlimitsbehaviorcomponent",
    "shoop_serviceprovider",
    "shoop_servicebehaviorcomponent",
    "shoop_paymentmethod_behavior_components",
    "shoop_shippingmethod_behavior_components",
    "shoop_customcarrier",
    "shoop_custompaymentprocessor",
    "shoop_serviceprovider_translation",
    "shoop_waivingcostbehaviorcomponent_translation",
    "shoop_fixedcostbehaviorcomponent_translation",
    "shoop_paymentmethod",
    "shoop_shippingmethod",
    "shoop_weightbasedpricingbehaviorcomponent",
    "shoop_weightbasedpricerange",
    "shoop_weightbasedpricerange_translation",
    "shoop_shipment",
    "shoop_contact",
    "shoop_groupavailabilitybehaviorcomponent",
    "shoop_groupavailabilitybehaviorcomponent_groups",
    "shoop_roundingbehaviorcomponent",
    "shoop_order",
    "shoop_staffonlybehaviorcomponent",
    "shoop_testing_expensiveswedenbehaviorcomponent",
    "shoop_testing_paymentwithcheckoutphase",
    "shoop_testing_pseudopaymentprocessor",
    "shoop_testing_carrierwithcheckoutphase",
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        with connection.cursor() as cursor:

            def run(statement, *args):
                cursor.execute(statement, args)

            for app in APP_LABELS:
                self.stdout.write("Updating migrations and content types for %s" % app)
                new_app = app.replace("shoop", "shuup")
                run("DELETE FROM django_migrations" " WHERE app=%s AND name != '0001_initial'", app)
                run("UPDATE django_migrations" " SET app=%s WHERE app=%s", new_app, app)
                run("UPDATE django_content_type" " SET app_label=%s WHERE app_label=%s", new_app, app)

            for table in TABLES:
                self.stdout.write("Renaming table %s" % table)
                new_table = table.replace("shoop", "shuup")
                run("ALTER TABLE %s RENAME TO %s" % (table, new_table))
