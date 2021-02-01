/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    let $contentBlocks = $(".content-block");
    let $contentWraps = $contentBlocks.find(".content-wrap");

    $(".toggle-contents").click(function(event) {
        const $collapseElement = $(this).closest(".content-block").find(".content-wrap");
        event.preventDefault();

        // Checks if the bootstrap collapse animation is not ongoing
        if (!$collapseElement.hasClass("collapsing")) {
            $collapseElement.collapse("toggle");
            $(this).closest(".title").toggleClass("open");
        }
    });
    $contentBlocks.each(function() {
        if ($(this).find(".has-error").length) {
            $(this).find(".block-title").addClass("mobile-error-indicator");
        }
    });

    // Activate first sidebar-list-item with errors
    $("a.sidebar-list-item.errors").first().trigger("click");

    // clear inline height: 0 on resize since we want blocks to be expanded on medium screens
    // this circumvents the need for !important in our css
    $(window).resize(_.debounce(function(){
        $contentWraps.css("height", "");
        $("#main-content").css("margin-top", $(".support-nav-wrap").height() + 15);
    }, 100));

    $(window).ready(function() {
        $("#main-content").css("margin-top", $(".support-nav-wrap").height() + 15);
    });
});
