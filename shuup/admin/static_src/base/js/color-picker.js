/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

var inputChangeTimeout;
function activateColorPicker(el) {
    $(el).colorpicker({
        format: "hex",
        horizontal: true,
        autoInputFallback: false,
    }).unbind("keyup").on("keyup", function(event) {
        window.clearTimeout(inputChangeTimeout);
        inputChangeTimeout = window.setTimeout(function () {
            $(event.target).trigger("change");
        }, 1000);
    });
}
window.activateColorPicker = activateColorPicker;

$(function() {
    $(".hex-color-picker").each((index, el) => {
        activateColorPicker(el);
    });
});
