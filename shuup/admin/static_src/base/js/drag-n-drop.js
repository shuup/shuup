/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.targetElement = null;
window.sourceElement = null;

const Sortable = require('sortablejs');

function updateOrdering(e) {
    var items = ""
    window.targetElement.find("input[type=checkbox]").each(function(idx, elem) {
       items += $(elem).attr("name") + "|";
    });
    $("#ordering").text(items);
}

function removeFromActive(e) {
    e.preventDefault();

    var label = $(this).data("label");
    var name = $(this).data("name");

    const $source = $("#target-placeholder li");
    const html = $source.html().replace(/NAME/g, name).replace(/LABEL/g, label);
    window.sourceElement.append($("<li>").html(html));
    $(this).closest("li").remove();
    updateOrdering();
}

function addToActive(e) {
    e.preventDefault();

    var label = $(this).data("label");
    var name = $(this).data("name");

    const $source = $("#source-placeholder li");
    const html = $source.html().replace(/NAME/g, name).replace(/LABEL/g, label);
    window.targetElement.append($("<li>").html(html));
    $(this).closest("li").remove();
    updateOrdering();
}

window.activateSortable = function(targetElement, sourceElement) {
    var $target = $("#" + targetElement);
    var $source = $("#" + sourceElement);
    window.targetElement = $target;
    window.sourceElement = $source;

    var el = document.getElementById(targetElement);
    var sortable = Sortable.create(el, {
        handle: ".sorting-handle",
        onEnd: function (/**Event*/evt) {
            updateOrdering();
        }
    });
    updateOrdering();
    $(document).on("click", ".btn-remove-sortable", removeFromActive);
    $(document).on("click", ".btn-add-sortable", addToActive);
};
