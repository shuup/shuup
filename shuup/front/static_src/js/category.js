/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

// CustomEvent polyfill
// https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/CustomEvent#Polyfill
if (typeof window.CustomEvent !== "function") {
    function CustomEvent(event, params) {
        params = params || { bubbles: false, cancelable: false, detail: null };
        var evt = document.createEvent('CustomEvent');
        evt.initCustomEvent(event, params.bubbles, params.cancelable, params.detail);
        return evt;
    }
    CustomEvent.prototype = window.Event.prototype;
    window.CustomEvent = CustomEvent;
}

// https://davidwalsh.name/javascript-debounce-function
function debounce(func, wait, immediate) {
    let timeout;
    return function () {
        let context = this, args = arguments;
        let later = function () {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        let callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

window.refreshFilters = debounce(function refreshFilters(pageNumber) {
    var pagination = $("ul.pagination");
    var state = { page: pageNumber ? pageNumber : 1 };
    $.each(window.PRODUCT_LIST_FILTERS, function (idx, key) {
        var filterObj = $("#id_" + key);

        if (!filterObj || filterObj.data("exclude")) {
            return;
        }

        if (filterObj.is("select")) {  // Basic select, checkbox etc...
            state[key] = filterObj.val();
        } else if (filterObj.is("input[type='text']")) {
            state[key] = filterObj.val();
        } else if (filterObj.is("input[type='hidden']")) {
            state[key] = filterObj.val();
        } else if (filterObj.is("input[type='number']")) {
            state[key] = filterObj.val();
        } else if (filterObj.is("input[type='checkbox']")) {
            state[key] = filterObj.prop("checked") ? 1 : 0;
        }
        else if (filterObj.is("div")) {  // Should be filter widget
            var values = [];
            filterObj.find("input:checked").each(function () {
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

    window.dispatchEvent(new CustomEvent("Shuup.FiltersRefreshed", {
        detail: {
            state,
            filterString
        }
    }));

    // prevent scroll to page buttons
    return false;
}, 150);

function serializeParams(obj) {
    const str = [];
    for (const param in obj) {
        if (obj.hasOwnProperty(param)) {
            if (Array.isArray(obj[param]) && !obj[param].length) {
                continue;
            }
            str.push(encodeURIComponent(param) + "=" + encodeURIComponent(obj[param]));
        }
    }
    return str.join("&");
}

function getFilterString(state) {
    const filters = {};
    Object.keys(state).filter(key => state[key]).forEach((key) => {
        filters[key] = state[key];
    });
    return "?" + serializeParams(filters);
}

function reloadProducts(filterString) {
    const $cont = $("#ajax_content");
    if ($cont.length === 0) {
        return;
    }
    const $prods = $(".products-wrap");
    const $adminMenu = $("#admin-tools-menu");
    const adminMenuHeight = ($adminMenu.length > 0) ? $adminMenu.height() : 0;
    const top = ($prods.length > 0) ? $prods.offset().top : $cont.offset().top;
    window.scrollTo(0, top - adminMenuHeight);

    // this is to ensure browser back/forward from different domain does a full refresh
    filterString += (filterString === "") ? "?" : "&";
    filterString += "ajax=1";
    $cont.load(location.pathname + filterString);
}

$(function () {
    window.addEventListener("popstate", function (e) {
        const filterString = getFilterString(e.state);
        reloadProducts(filterString);
        window.dispatchEvent(new CustomEvent("Shuup.FiltersRefreshed", {
            detail: {
                state: e.state,
                filterString
            }
        }));
    });

    $.each(window.PRODUCT_LIST_FILTERS, function (idx, key) {
        const $field = $("#id_" + key);

        if ($field.parent(".form-group").hasClass("has-error")) {
            const host_str = '//' + location.host + location.pathname;
            window.location.href = host_str;
        }
        if (!$field.data("no-auto-update")) {
            $field.on("change", function () {
                window.refreshFilters(window.PAGE_NUMBER);
            });
        }
    });
});
