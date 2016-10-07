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


REGION_CHANGER_JS = """
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
        $regionField.val("");
        $regionCodeField.closest("div.form-group").hide();
    }
}

function updateRegion(field) {
    var countryField = field + "-country";
    var regionField = field + "-region";
    var regionCode = field + "-region_code";
    if (field == "") {
        countryField = "#id_country";
        regionField = "#id_region";
        regionCode = "#id_region_code";
    }
    var country = $(countryField).val();
    var regionsData = window.REGIONS[country];
    handleRegionFields(regionField, regionCode, regionsData);
}
"""


CHANGER_FUNCTIONS = """
$(function(){
    updateRegion("%(region_field_prefix)s");
    if("%(region_field_prefix)s" != "") {
        $("%(region_field_prefix)s-country").on("change", function() {
            updateRegion("%(region_field_prefix)s");
        });
    }
    else {
        $("#id_country").on("change", function() {
            updateRegion("");
        });
    }
});
"""


def add_resources(context, placement="body_end", fields=[""]):
    add_resource(context, placement, InlineScriptResource(REGIONS % {"regions": json.dumps(regions_data)}))
    add_resource(context, placement, InlineScriptResource(REGION_CHANGER_JS))
    for field in fields:
        add_resource(context, placement, InlineScriptResource(CHANGER_FUNCTIONS % {"region_field_prefix": field}))


def add_front_resources(context, content):
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    if not view_class:
        return
    view_name = getattr(view_class, "__name__", "")
    if view_name in ["AddressesPhase", "SingleCheckoutPhase"]:  # For front
        add_resources(context, fields=["#id_billing", "#id_shipping"])
    elif view_name == "ContactEditView":  # For admin contact edit
        add_resources(context, fields=["#id_billing_address", "#id_shipping_address"])
    elif view_name == "OrderEditView":  # For admin order editor only regions is enough
        add_resource(context, "body_end", InlineScriptResource(REGIONS % {"regions": json.dumps(regions_data)}))
    elif view_name in ["AddressBookEditView"]:
        add_resources(context, fields=["#id_address"])
    elif view_name in ["WizardView"]:
        add_resource(context, "body_end", InlineScriptResource(REGIONS % {"regions": json.dumps(regions_data)}))
