/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function () {
    const $dropdowns = $(".dropdown");
    // Add slideUp/slideDown animations to all bootstrap dropdowns
    $dropdowns.on("show.bs.dropdown", function () {
        $(this).find(".dropdown-menu").first().stop(true, true).slideDown(200, "easeInSine");
    }).on("hide.bs.dropdown", function () {
        $(this).find(".dropdown-menu").first().stop(true, true).slideUp(300, "easeOutSine");
    });
});
