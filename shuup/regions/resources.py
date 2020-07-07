# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.utils.static import get_shuup_static_url
from shuup.xtheme.resources import add_resource, InlineScriptResource

INITIALIZE_FIELDS_FUNCTION = """
window.initializeRegionFields('%(country_code_field)s', '%(region_code_field)s', '%(region_field)s');
"""


def add_init_fields_resource(context, country_code_field, region_code_field, region_field=None, placement="body_end"):
    add_resource(context, placement, InlineScriptResource(
        INITIALIZE_FIELDS_FUNCTION % {
            "country_code_field": country_code_field,
            "region_code_field": region_code_field,
            "region_field": region_field if region_field else ""
        })
    )


def add_front_resources(context, content):
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    if not view_class:
        return

    view_name = getattr(view_class, "__name__", "")

    # For front
    if view_name in ["CheckoutMethodPhase", "CompanyRegistrationView", "CustomerEditView", "CompanyEditView"]:
        add_resource(context, "body_end", get_shuup_static_url("shuup-regions.js"))
        add_init_fields_resource(context, "#id_billing-country", "#id_billing-region_code", "#id_billing-region")
        add_init_fields_resource(context, "#id_shipping-country", "#id_shipping-region_code", "#id_shipping-region")

    elif view_name in ["AddressesPhase"]:
        # the address phase can be requested through ajax
        # when ajax request, we should append the scripts at the end of the content
        # and not at the body end, as there is no body element in the ajax response
        placement = "body_end"
        request = context.get("request")
        if request and request.is_ajax():
            placement = "content_end"

        add_resource(context, placement, get_shuup_static_url("shuup-regions.js"))
        add_init_fields_resource(
            context,
            "#id_billing-country",
            "#id_billing-region_code",
            "#id_billing-region",
            placement
        )
        add_init_fields_resource(
            context,
            "#id_shipping-country",
            "#id_shipping-region_code",
            "#id_shipping-region",
            placement
        )

    # For admin views
    elif view_name in ["ContactEditView", "OrderAddressEditView"]:
        add_resource(context, "body_end", get_shuup_static_url("shuup-regions.js"))
        add_init_fields_resource(
            context,
            "#id_billing_address-country",
            "#id_billing_address-region_code",
            "#id_billing_address-region"
        )
        add_init_fields_resource(
            context,
            "#id_shipping_address-country",
            "#id_shipping_address-region_code",
            "#id_shipping_address-region"
        )

    # For admin order editor only regions is enough
    elif view_name == "OrderEditView":
        add_resource(context, "body_end", get_shuup_static_url("shuup-regions.js"))

    elif view_name in ["AddressBookEditView", "WizardView", "ShopEditView", "SupplierEditView"]:
        add_resource(context, "body_end", get_shuup_static_url("shuup-regions.js"))
        add_init_fields_resource(context, "#id_address-country", "#id_address-region_code", "#id_address-region")
