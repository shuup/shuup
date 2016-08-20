/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.updatePrice = function updatePrice(productId) {
    var $quantity = $("#product-quantity");
    if ($quantity.length === 0 || !$quantity.is(":valid")) {
        return;
    }

    var data = {
        // In case productId is not available try to fallback to first input with correct name
        id: productId ? productId : $("input[name=product_id]").val(),
        quantity: $quantity.val()
    };

    var $simpleVariationSelect = $("#product-variations");
    if ($simpleVariationSelect.length > 0) {
        // Smells like a simple variation; use the selected child's ID instead.
        data.id = $simpleVariationSelect.val();
    } else {
        // See if we have variable variation select boxes; if we do, add those.
        $("select.variable-variation").serializeArray().forEach(function(obj) {
            data[obj.name] = obj.value;
        });
    }
    jQuery.ajax({url: "/xtheme/product_price", dataType: "html", data: data}).done(function(responseText) {
        var $content = jQuery("<div>").append(jQuery.parseHTML(responseText)).find("#product-price-div");
        jQuery("#product-price-div").replaceWith($content);
        if ($content.find("#no-price").length > 0) {
            $("#add-to-cart-button").prop("disabled", true);
        } else {
            $("#add-to-cart-button").not(".not-orderable").prop("disabled", false);
        }
    });
};
