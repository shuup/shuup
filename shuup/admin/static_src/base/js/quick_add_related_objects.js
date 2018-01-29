/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

window.addToSelect2 = function addToSelect2(target, value, name) {
    const newOption = new Option(name, value, true, true);
    $("select[name='" + target + "']").append(newOption).trigger('change');

    // Product update or create
    if (target.includes("primary_category")) {
        const categories = $("select[name*='categories']");
        if (categories.length > 0) {
            const newOption = new Option(name, value, true, true);
            categories.append(newOption).trigger('change');
        }
    }

    window.closeQuickAddIFrame();
};

window.closeQuickAddIFrame = function closeQuickAddIFrame(e) {
    if (e !== undefined) {
        e.preventDefault();
    }
    $("#create-object-overlay").remove();
};

$(function() {
    $('.quick-add-btn a.btn').on("click", function(e) {
        e.preventDefault();
        window.closeQuickAddIFrame();
        const url = $(this).data("url");
        const overlay = document.createElement("div");
        overlay.id = "create-object-overlay";

        const contentPane = document.createElement('div');
        contentPane.id = "create-object-content-pane"
        contentPane.className = "content-pane";
        overlay.appendChild(contentPane);

        const closeIcon = document.createElement("i");
        closeIcon.className = "fa fa-times-circle-o fa-3x text-danger";
        const closeButton = document.createElement("a");
        closeButton.className = "close-btn";
        closeButton.href = "#";
        closeButton.onclick = window.closeQuickAddIFrame;
        closeButton.appendChild(closeIcon);
        contentPane.appendChild(closeButton);

        const iframe = document.createElement('iframe');
        iframe.frameBorder=0;
        iframe.width="100%";
        iframe.height="100%";
        iframe.id="create-object-iframe";

        iframe.onload = function() {
            $("#create-object-content-pane").addClass("open");
        };

        iframe.setAttribute("src", url);
        contentPane.appendChild(iframe);
        $(document.body).append(overlay);
    });
});
