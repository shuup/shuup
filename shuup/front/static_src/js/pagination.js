/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.moveToPage = function moveToPage(pageNumber) {
    var pagination = $("ul.pagination");
    var state = {
        sort: $("#id_sort").val(),
        page: pageNumber
    };
    var filterString = getFilterString(state);
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
    reloadProducts(filterString);

    if(window.history && window.history.pushState) {
        history.pushState(state, null, filterString);
    }
    // prevent scroll to page buttons
    return false;
};

function getFilterString(state) {
    var filterString = "";
    if(state !== null) {
        filterString = "?sort=" + state.sort + "&page=" + state.page;
    }
    return filterString;
}

function reloadProducts(filterString) {
    // this is to ensure browser back/forward from different domain does a full refresh
    filterString += (filterString == "")? "?" : "&";
    filterString += "ajax=1";

    window.scrollTo(0, 0);
    $("#ajax_content").load(location.pathname + filterString);
}

$(function() {
    window.addEventListener('popstate', function(e) {
        reloadProducts(getFilterString(e.state));
    });
});
