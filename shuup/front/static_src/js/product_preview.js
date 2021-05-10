/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.showPreview = function showPreview(productId) {
    var modalSelector = "#product-" + productId + "-modal";
    var $productModal = $(modalSelector);
    if ($productModal.length) {
        $productModal.modal("show");
        return;
    }

    // make sure modals disappear and are not "cached"
    $(document).on("hidden.bs.modal", modalSelector, function () {
        $(modalSelector).remove();
    });

    $.ajax({
        url: "/xtheme/product_preview",
        method: "GET",
        data: { id: productId },
        success: function (data) {
            $("body").append(data);
            $(modalSelector).modal("show");
            window.updatePrice(productId);
            $(".selectpicker").selectpicker();
        }
    });
};
