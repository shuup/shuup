/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    DashboardCharts.init();
    var msnry = new Masonry(document.getElementById("dashboard-wrapper"), {
        itemSelector: ".block",
        columnWidth: ".block"
    });
    $(document).on("click", "button.dismiss-button", function() {
        var $button = $(this);
        var url = $button.data("dismissUrl");
        if(!url) return;
        $.ajax({
            type: "POST",
            url: url,
            dataType: "json",
            success: function(data) {
                if(data.ok) {
                    var dismissTarget = $button.data("dismissTarget");
                    if(dismissTarget) $(dismissTarget).remove();
                }
                if(data.error) Messages.enqueue({text: data.error});
            }
        });
    });


});
