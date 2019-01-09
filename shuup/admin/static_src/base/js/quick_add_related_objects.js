/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

"use strict";

window.addToSelect2 = function addToSelect2(target, value, name) {
    var newOption = new Option(name, value, true, true);
    $("select[name='" + target + "']").append(newOption).trigger("change");

    // Product update or create
    if (target.includes("primary_category")) {
        var categories = $("select[name*='categories']");
        if (categories.length > 0) {
            newOption = new Option(name, value, true, true);
            categories.append(newOption).trigger("change");
        }
    }

    window.closeQuickIFrame();
};

window.closeQuickIFrame = function () {
    $("#create-object-overlay").remove();
};

function createQuickIframe(url) {
    window.closeQuickIFrame();
    const overlay = document.createElement("div");
    overlay.id = "create-object-overlay";

    const contentPane = document.createElement("div");
    contentPane.id = "create-object-content-pane";
    contentPane.className = "content-pane";
    overlay.appendChild(contentPane);

    const topBar = document.createElement("div");
    topBar.className = "top-bar";

    const closeIcon = document.createElement("i");
    closeIcon.className = "fa fa-times fa-2x";
    const closeButton = document.createElement("a");
    closeButton.className = "close-btn";
    closeButton.href = "#";
    closeButton.onclick = function (e) {
        if (e !== undefined) {
            e.preventDefault();
        }
        window.closeQuickIFrame();
    };
    closeButton.appendChild(closeIcon);
    topBar.appendChild(closeButton);
    contentPane.appendChild(topBar);

    const iFrame = document.createElement("iframe");
    iFrame.frameBorder = 0;
    iFrame.width = "100%";
    iFrame.height = "100%";
    iFrame.id = "create-object-iframe";

    iFrame.onload = function() {
        $("#create-object-content-pane").addClass("open");
        $("#create-object-iframe").contents().find(".quick-add-btn").remove();
        $("#create-object-iframe").contents().find(".edit-object-btn").remove();
    };

    iFrame.setAttribute("src", url);
    contentPane.appendChild(iFrame);
    $(document.body).append(overlay);
}
window.createQuickAddIframe = createQuickIframe;

window.setupQuickAdd = function (element) {
    $(element).parent().siblings(".select2-container").addClass("has-quick-btn");
    $(element).on("click", function(e) {
        e.preventDefault();
        createQuickIframe($(this).data("url"));
    });
};

window.setupEditButton = function (element) {
    // setup each target
    $(element).parent().siblings(".select2-container").addClass("has-quick-btn");
    $(element).each(function () {
        $(element).siblings(".select2-container").addClass("has-quick-btn");
        var target = this;
        var selectTarget = $(target).data("target");

        if (selectTarget) {
            var field = $("[name='" + selectTarget + "']");

            if (!field.val()) {
                $(target).hide();
            }

            field.on("change", function () {
                if ($(this).val()) {
                    $(target).show();
                } else {
                    $(target).hide();
                }
            });
        }
    });
    $(element).on("click", function(e) {
        e.preventDefault();
        var selectTarget = $(e.currentTarget).data("target");
        if (selectTarget) {
            var field = $("[name='" + selectTarget + "']");
            var model = $(e.currentTarget).data("edit-model");
            var selectedValue = $(field).val();
            if (selectedValue) {
                var url = window.ShuupAdminConfig.browserUrls.edit + "?mode=iframe&model=" + model + "&id=" + selectedValue;
                createQuickIframe(url);
            }
        }
    });
};

$(function() {
    window.setupQuickAdd($(".quick-add-btn a.btn"));
    window.setupEditButton($(".edit-object-btn a.btn"));
});
