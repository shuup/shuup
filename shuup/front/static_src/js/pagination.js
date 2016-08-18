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
