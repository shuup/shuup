/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { debounce } from "./utils";

// CustomEvent polyfill
// https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/CustomEvent#Polyfill
function CustomEvent(event, params) {
    params = params || { bubbles: false, cancelable: false, detail: null };
    const evt = document.createEvent("CustomEvent");
    evt.initCustomEvent(event, params.bubbles, params.cancelable, params.detail);
    return evt;
}
if (typeof window.CustomEvent !== "function") {
    CustomEvent.prototype = window.Event.prototype;
    window.CustomEvent = CustomEvent;
}

// This is the target selector of the element that will be used
// to scroll the page to when the the list gets loaded
// Set this to `null` to not auto scroll when products are loaded
window.ProductListScrollTarget = ".products-wrap";

window.refreshFilters = debounce(function refreshFilters(pageNumber = 1) {
    const pagination = $("ul.pagination");
    const currentState = new URLSearchParams(window.location.search);
    const state = {};

    for (let key of currentState.keys()) {
        state[key] = currentState.get(key);
    }

    state.page = pageNumber || 1;

    if (!window.PRODUCT_LIST_FILTERS) {
        return;
    }
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

    reloadProducts(filterString, () => {
        pagination.prop("disabled", false);
    });

    if (window.history && window.history.pushState) {
        history.replaceState(state, null, filterString);
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

function reloadProducts(filterString, onComplete = null) {
    const $cont = $("#ajax_content");
    if ($cont.length === 0) {
        onComplete();
        return;
    }
    // this is to ensure browser back/forward from different domain does a full refresh
    filterString += (filterString === "") ? "?" : "&";
    filterString += "ajax=1";

    // warn that the product list will be loaded
    window.dispatchEvent(new CustomEvent("Shuup.LoadProductList", {
        detail: {
            filterString
        }
    }));

    $.get(location.pathname + filterString, function (data) {
        $cont.replaceWith(data);

        if (window.ProductListScrollTarget) {
            const $prods = $(window.ProductListScrollTarget);
            const $adminMenu = $("#admin-tools-menu");
            const adminMenuHeight = ($adminMenu.length > 0) ? $adminMenu.height() : 0;
            const top = ($prods.length > 0) ? $prods.offset().top : $cont.offset().top;
            $("html, body").stop().animate({ scrollTop: top - adminMenuHeight }, 300, "swing");
        }
        window.dispatchEvent(new CustomEvent("Shuup.ProductListLoaded", {
            detail: {
                filterString,
                data
            }
        }));
        if (onComplete) {
            onComplete();
        }
    });
}

$(function () {
    window.addEventListener("popstate", function (e) {
        if (e.state) {
            const filterString = getFilterString(e.state);
            reloadProducts(filterString);
            window.dispatchEvent(new CustomEvent("Shuup.FiltersRefreshed", {
                detail: {
                    state: e.state,
                    filterString
                }
            }));
        }
    });

    $.each(window.PRODUCT_LIST_FILTERS, function (idx, key) {
        const $field = $("#id_" + key);

        if ($field.parent(".form-group").hasClass("has-error")) {
            const hostStr = "//" + location.host + location.pathname;
            window.location.href = hostStr;
        }
        if (!$field.data("no-auto-update")) {
            $field.on("change", function () {
                window.refreshFilters(window.PAGE_NUMBER);
            });
        }
    });
});
