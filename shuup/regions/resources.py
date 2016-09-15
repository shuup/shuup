# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json

from shuup.xtheme.resources import add_resource, InlineScriptResource

from .data import regions_data


REGIONS = """
window.REGIONS = %(regions)s;
"""


REGION_CHANGER_JS = REGIONS + """
$(function(){
    function handleRegionFields(regionSelector, regionCodeSelector, regionsData) {
        var $regionField = $(regionSelector);
        var $regionCodeField = $(regionCodeSelector);
        if (regionsData) {
            $regionField.closest(".form-group").hide();
            $regionCodeField.closest(".form-group").show();
            var regionValue = $regionCodeField.val();
            $newRegionField = $("<select/>", {
                id: $regionCodeField.attr("id"),
                name: $regionCodeField.attr("name"),
                class: "form-control"
            });
            $regionCodeField.replaceWith($newRegionField);
            $option = $("<option/>", {
                value: "",
                text: "---------"
            });
            $newRegionField.append($option);
            $.each(regionsData, function(idx, region) {
                $option = $("<option/>", {
                    value: region.code,
                    text: region.name,
                    selected: (regionValue == region.code ? true : false)
                });
                $newRegionField.append($option);
            });
            $newRegionField.on("change", function() {
                $(regionSelector).val($(this).val());
            });
        } else {
            $regionField.closest("div.form-group").show();
            $regionCodeField.val("");
            $regionCodeField.closest("div.form-group").hide();
        }
    }

    function updateBillingRegion() {
        var country = $("%(billing_field_prefix)s-country").val();
        var regionsData = window.REGIONS[country];
        handleRegionFields("%(billing_field_prefix)s-region", "%(billing_field_prefix)s-region_code", regionsData);
    }

    function updateShippingRegion() {
        var country = $("%(shipping_field_prefix)s-country").val();
        var regionsData = window.REGIONS[country];
        handleRegionFields("%(shipping_field_prefix)s-region", "%(shipping_field_prefix)s-region_code", regionsData);
    }

    updateBillingRegion();
    updateShippingRegion();
    $("%(billing_field_prefix)s-country").change(updateBillingRegion);
    $("%(shipping_field_prefix)s-country").change(updateShippingRegion);
});
"""


def add_front_resources(context, content):
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    if not view_class:
        return

    if getattr(view_class, "__name__", "") == "AddressesPhase":  # For front
        add_resource(context, "body_end", InlineScriptResource(REGION_CHANGER_JS % {
            "billing_field_prefix": "#id_billing",
            "shipping_field_prefix": "#id_shipping",
            "regions": json.dumps(regions_data)
        }))
    if getattr(view_class, "__name__", "") == "ContactEditView":  # For admin contact edit
        add_resource(context, "body_end", InlineScriptResource(REGION_CHANGER_JS % {
            "billing_field_prefix": "#id_billing_address",
            "shipping_field_prefix": "#id_shipping_address",
            "regions": json.dumps(regions_data)
        }))
    if getattr(view_class, "__name__", "") == "OrderEditView":  # For admin order editor only regions is enough
        add_resource(context, "body_end", InlineScriptResource(REGIONS % {"regions": json.dumps(regions_data)}))
