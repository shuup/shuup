/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function isTouchDevice() {
  return ("ontouchstart" in window || navigator.maxTouchPoints);
}

$(function() {
    "use strict";
    $("[data-toggle='popover']").each(function(idx, elem) {
        if($(elem).data("trigger") !== "manual") {
            $(elem).popover();
        } else if (!isTouchDevice()) {
            $(elem).on("mouseenter", function() {
                $(elem).popover("show");
            });
            $(elem).on("mouseleave", function() {
                $(elem).popover("hide");
            });
        } else {
            // unbind all hover related from manual popovers on touch device
            $(elem).unbind("hover mouseenter mouseleave");
        }
    });
}());
