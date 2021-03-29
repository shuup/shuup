/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function changeLanguage() {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = window.ShuupAdminConfig.browserUrls.setLanguage;
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "language";
    input.id = "language-field";
    input.value = $(this).data("value");
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
}

$(function(){
    "use strict";
    $(".languages a").click(changeLanguage);
});
