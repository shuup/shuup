/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.refreshFilters = function refreshFilters(pageNumber) {
    var pagination = $("ul.pagination");
    var state = {page: pageNumber ? pageNumber : 1};
    $.each(window.PRODUCT_LIST_FILTERS, function(idx, key) {
        var filterObj = $("#id_" + key);
        if (filterObj.is("select")) {  // Basic select, checkbox etc...
            state[key] = filterObj.val();
        } else if (filterObj.is("div")) {  // Should be filter widget
            var values = [];
            filterObj.find("input:checked").each(function() {
                values.push($(this).val());
            });
            state[key] = values;
        }
    });

    var filterString = getFilterString(state);
    if (pagination.length > 0) {
        // Prevent double clicking when ajax is loading
        if (pagination.prop("disabled")) {
            return false;
        }
        pagination.prop("disabled", true);

        if (typeof (pageNumber) !== "number") {
            pageNumber = parseInt(pageNumber);
            if (isNaN(pageNumber)) {
                return false;
            }
        }
        window.PAGE_NUMBER = pageNumber;
    }


    reloadProducts(filterString);

    if (window.history && window.history.pushState) {
        history.pushState(state, null, filterString);
    }
    // prevent scroll to page buttons
    return false;
};

function getFilterString(state) {
    var filterString = "";
    if(state !== null) {
        filterString = "?";
        $.each(state, function(key, value) {
            filterString += (filterString.endsWith("?") || filterString.endsWith("&") ? "" : "&");
            if (value.constructor === Array) {
                filterString += (value.length > 0 ? (key + "=" + value.join("&" + key + "=")) : "");
            } else {
                filterString += (value ? key + "=" + value: "");
            }
        });
    }
    return filterString;
}

function reloadProducts(filterString) {
    // this is to ensure browser back/forward from different domain does a full refresh
    filterString += (filterString === "") ? "?" : "&";
    filterString += "ajax=1";
    window.scrollTo(0, $(".products-wrap").offset().top);
    $("#ajax_content").load(location.pathname + filterString);
}

$(function() {
    window.addEventListener("popstate", function(e) {
        reloadProducts(getFilterString(e.state));
    });

    $.each(window.PRODUCT_LIST_FILTERS, function(idx, key) {
        if($("#id_" + key).parent(".form-group").hasClass("has-error")) {
            const host_str = '//' + location.host + location.pathname;
            window.location.href = host_str;
        }
        $("#id_" + key).on("change", function() {
            window.refreshFilters(window.PAGE_NUMBER);
        });
    });
});
