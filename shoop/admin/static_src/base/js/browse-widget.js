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
        var $text = info.$container.find(".browse-text");
        $text.text(obj.text);
        $text.prop("href", obj.url || "#");
        delete browseData[data.pick.id];
    }, false);

    $(document).on("click", ".browse-widget .browse-btn", function() {
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

    $(document).on("click", ".browse-widget .clear-btn", function() {
        var $container = $(this).closest(".browse-widget");
        if(!$container.length) return;
        var emptyText = $container.data("empty-text") || "";
        $container.find("input").val("");
        var $text = $container.find(".browse-text");
        $text.text(emptyText);
        $text.prop("href", "#");
    });

    $(document).on("click", ".browse-widget .browse-text", function(event) {
        var href = $(this).prop("href");
        if(/#$/.test(href)) {  // Looks empty, so prevent clicks
            event.preventDefault();
            return false;
        }
    });
});
