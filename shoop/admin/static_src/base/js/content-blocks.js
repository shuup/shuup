/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".toggle-contents").click(function(event) {
        const $collapseElement = $(this).closest(".content-block").find(".content-wrap");
        event.preventDefault();

        // Checks if the bootstrap collapse animation is not ongoing
        if (!$collapseElement.hasClass("collapsing")) {
            $collapseElement.collapse("toggle");
            $(this).closest(".title").toggleClass("open");
        }
    });
    $(".content-block").each(function() {
        if ($(this).find(".has-error").length) {
            $(this).find(".block-title").addClass("mobile-error-indicator");
        }
    });

    // Activate first sidebar-list-item with errors
    $("a.sidebar-list-item.errors").first().trigger("click");
});
