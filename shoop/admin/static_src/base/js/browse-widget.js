/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/**
 * Support for media browsing widgets.
 * Currently opens a real, actual, true-to-1998
 * popup window (just like the Django admin, mind)
 * but could just as well use an <iframe> modal.
 */
$(function() {
    var browseData = {};

    window.addEventListener("message", function(event) {
        var data = event.data;
        if (!data.pick) return;
        var info = browseData[data.pick.id];
        if (!info) return;
        info.popup.close();
        var obj = data.pick.object;
        if (!obj) return;
        info.$container.find("input").val(obj.id);
        var $mediaText = info.$container.find(".browse-text");
        $mediaText.text(obj.text);
        $mediaText.prop("href", obj.url || "#");
        delete browseData[data.pick.id];
    }, false);

    $(".browse-btn").on("click", function() {
        var $container = $(this).closest(".browse-widget");
        if(!$container.length) return;
        var kind = $container.data("browse-kind");
        var browserUrl = window.ShoopAdminConfig.browserUrls[kind];
        if(!browserUrl) {
            alert("Error: No browser URL for kind: " + kind);
            return false;
        }
        var id = "m-" + (+new Date);
        var popup = window.open(
            browserUrl + (browserUrl.indexOf("?") > -1 ? "&" : "?") + "popup=1&pick=" + id,
            "browser_popup_" + id,
            "resizable,menubar=no,location=no"
        );
        browseData[id] = {
            $container: $container,
            popup: popup
        };
    });
});
