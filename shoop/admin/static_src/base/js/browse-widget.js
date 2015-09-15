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
    const browseData = {};

    window.addEventListener("message", function(event) {
        const data = event.data;
        if (!data.pick) {
            return;
        }
        const info = browseData[data.pick.id];
        if (!info) {
            return;
        }
        info.popup.close();
        const obj = data.pick.object;
        if (!obj) {
            return;
        }
        info.$container.find("input").val(obj.id);
        const $text = info.$container.find(".browse-text");
        $text.text(obj.text);
        $text.prop("href", obj.url || "#");
        delete browseData[data.pick.id];
    }, false);

    $(document).on("click", ".browse-widget .browse-btn", function() {
        const $container = $(this).closest(".browse-widget");
        if(!$container.length) {
            return;
        }
        const kind = $container.data("browse-kind");
        const filter = $container.data("filter");
        const browserUrl = window.ShoopAdminConfig.browserUrls[kind];
        if(!browserUrl) {
            alert("Error: No browser URL for kind: " + kind);
            return false;
        }
        const id = "m-" + (+new Date);
        const qs = _.compact([
            "popup=1",
            "pick=" + id,
            (filter ? "filter=" + filter : null)
        ]).join("&");
        const popup = window.open(
            browserUrl + (browserUrl.indexOf("?") > -1 ? "&" : "?") + qs,
            "browser_popup_" + id,
            "resizable,menubar=no,location=no"
        );
        browseData[id] = {
            $container: $container,
            popup: popup
        };
    });

    $(document).on("click", ".browse-widget .clear-btn", function() {
        const $container = $(this).closest(".browse-widget");
        if(!$container.length) {
            return;
        }
        const emptyText = $container.data("empty-text") || "";
        $container.find("input").val("");
        const $text = $container.find(".browse-text");
        $text.text(emptyText);
        $text.prop("href", "#");
    });

    $(document).on("click", ".browse-widget .browse-text", function(event) {
        const href = $(this).prop("href");
        if(/#$/.test(href)) {  // Looks empty, so prevent clicks
            event.preventDefault();
            return false;
        }
    });
});
