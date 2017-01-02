/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(document).ready(function() {
    var MAX_NUM_PRODUCTS = 5;

    function getRecentlyViewedProductIds(){
        var ids = decodeURIComponent(document.cookie.replace(new RegExp("(?:(?:^|.*;)\\s*" + encodeURIComponent("rvp").replace(/[\-\.\+\*]/g, "\\$&") + "\\s*\\=\\s*([^;]*).*$)|^.*$"), "$1")) || '';
        if(ids !== "") {
            return ids.split(",");
        } else {
            return [];
        }
    }

    function setRecentlyViewedProductIds(ids) {
        var expirationDate = new Date();
        var cookie = '';
        expirationDate.setFullYear(expirationDate.getFullYear() + 1);
        cookieString = "rvp=" + ids.join(",") + "; path=/; expires=" + expirationDate.toUTCString();
        document.cookie = cookieString;
    }

    function getCurrentId() {
        var currentId = parseInt(window.location.pathname.match(/[\d]+/));
        if(isNaN(currentId)) {
            return "";
        } else {
            return "" + currentId;
        }
    }

    var ids = getRecentlyViewedProductIds();
    var currentId = getCurrentId();
    if(currentId && ids.indexOf(currentId) < 0){
        ids.unshift(currentId);
        if(ids.length > MAX_NUM_PRODUCTS) {
            ids = ids.slice(0, -1);
        }
        setRecentlyViewedProductIds(ids);
    }
});
