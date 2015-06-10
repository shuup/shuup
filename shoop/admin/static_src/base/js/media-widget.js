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
    var mediaBrowse = {enabled: false};
    $(".media-browse").on("click", function() {
        var $container = $(this).closest(".media-widget");
        var id = "m-" + (+new Date);
        var popup = window.open(
            window.ShoopAdminConfig.mediaBrowserUrl + "?popup=1&pick=" + id,
            "mediapopup_" + id,
            "resizable,menubar=no,location=no"
        );
        mediaBrowse[id] = {
            $container: $container,
            popup: popup
        };
        if (!mediaBrowse.enabled) {
            window.addEventListener("message", function(event) {
                var data = event.data;
                if (!data.pick) return;
                var info = mediaBrowse[data.pick.id];
                if (!info) return;
                info.popup.close();
                info.$container.find("input").val(data.pick.file.id);
                var $mediaText = info.$container.find(".media-text");
                $mediaText.text(data.pick.file.name);
                $mediaText.prop("href", data.pick.file.url);

            }, false);

            mediaBrowse.enabled = true;
        }
    });
});
