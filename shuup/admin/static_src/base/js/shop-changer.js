/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function getInput(type, name, id, value) {
    const input = document.createElement("input");
    input.type = type;
    input.name = name;
    input.id = id;
    input.value = value;
    return input;
}

function changeShop() {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = window.ShuupAdminConfig.browserUrls.setShop;
    form.appendChild(getInput("hidden", "shop", "shop", $(this).val()));
    form.appendChild(getInput("hidden", "next", "next", window.location));
    document.body.appendChild(form);
    form.submit();
}

$(function(){
    "use strict";
    $("select.shop-changer").change(changeShop);
});
