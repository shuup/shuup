/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
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
    $(document).on("hidden.bs.modal", modalSelector, function() {
        $(modalSelector).remove();
    });

    $.ajax({
        url: "/xtheme/product_preview",
        method: "GET",
        data: {
            id: productId
        },
        success: function(data) {
            $("body").append(data);
            $(modalSelector).modal("show");
            updatePrice();
            $(".selectpicker").selectpicker();
        }
    });
};

window.singleSubmitForm = function($form) {
    var canSubmit = true;
    $form.submit(function() {
        if(canSubmit) {
            canSubmit = false;
        }
        else {
            return false;
        }
    });
};

function setProductListViewMode(isInListMode) {
    if (typeof (Storage) !== "undefined") {
        localStorage.setItem("product_list_view_list_mode", (isInListMode ? "list" : "grid"));
    }
}

function getProductListViewMode() {
    if (typeof (Storage) !== "undefined") {
        return localStorage.getItem("product_list_view_list_mode");
    }
    return "grid";
}

window.moveToPage = function moveToPage(pageNumber) {
    var pagination = $("ul.pagination");

    // Prevent double clicking when ajax is loading
    if (pagination.prop("disabled")) {
        return false;
    }
    pagination.prop("disabled", true);

    if (typeof (pageNumber) !== "number") {
        pageNumber = parseInt(pageNumber);
        if (isNaN(pageNumber)) {
            return;
        }
    }
    window.PAGE_NUMBER = pageNumber;

    reloadProducts();
};

function reloadProducts() {
    var filterString = "?sort=" + $("#id_sort").val() + "&page=" + window.PAGE_NUMBER;
    $("#ajax_content").load(location.pathname + filterString);
}

function updatePrice() {
    var $quantity = $("#product-quantity");
    if ($quantity.length === 0 || !$quantity.is(":valid")) {
        return;
    }

    var data = {
        id: $("input[name=product_id]").val(),
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
}

function changeLanguage() {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/set-language/";
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "language";
    input.id = "language-field";
    input.value = $(this).data("value");
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
}

$(function() {
    $("#search-modal").on("show.bs.modal", function() {
        setTimeout(function() {
            $("#site-search").focus();
        }, 300);
    });

    function openMobileNav() {
        $(document.body).addClass("menu-open");
    }

    function closeMobileNav() {
        $(document.body).removeClass("menu-open");
    }

    function mobileNavIsOpen() {
        return $(document.body).hasClass("menu-open");
    }

    $(".toggle-mobile-nav").click(function(e) {
        e.stopPropagation();
        if (mobileNavIsOpen()) {
            closeMobileNav();
        } else {
            openMobileNav();
        }
    });

    $(document).click(function(e) {
        if (mobileNavIsOpen() && !$(e.target).closest(".pages .nav-collapse").length) {
            closeMobileNav();
        }

    });

    $(".main-nav .dropdown-menu").click(function(e) {
        e.stopPropagation();
    });

    $("#product-list-view-type").on("change", function() {
        var $productListView = $(".product-list-view");
        $productListView.toggleClass("list");
        setProductListViewMode($productListView.hasClass("list"));
    });

    $(".selectpicker").selectpicker();

    // By default product list view is in grid mode
    var $productListView = $(".product-list-view");
    if ($productListView.length > 0 && getProductListViewMode() === "list") {
        $productListView.addClass("list");
        $("#product-list-view-type").prop("checked", true);
    }

    // Add proper classes to category navigation based on current-page class
    var $currentlySelectedPage = $(".current-page");
    if ($currentlySelectedPage.length > 0) {
        $currentlySelectedPage.addClass("current");
        $currentlySelectedPage.parents("li").addClass("current");
    }

    $(document).on("change", ".variable-variation, #product-variations, #product-quantity", updatePrice);
    updatePrice();
    $(".languages li a").click(changeLanguage);
});
