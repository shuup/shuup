/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".toggle-contents").click(function(e) {
        var $collapseElement = $(this).closest(".content-block").find(".content-wrap");
        e.preventDefault();
        // Checks if the bootstrap collapse animation is not ongoing
        if (!$collapseElement.hasClass("collapsing")) {
            $collapseElement.collapse("toggle");
            $(this).closest(".title").toggleClass("open");
        }
    });
}());
