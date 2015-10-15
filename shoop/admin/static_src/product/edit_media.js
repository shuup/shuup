/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".product-media-delete").on("click", function(e) {
        e.preventDefault();
        if (confirm("Are you sure you want to delete this media?"))
        {
            $(this).parents(".panel").fadeOut();
            $(this).next(".hide").find("input").prop("checked", true);
        }
    });

    $(document).on("click", ".set-as-primary", function(e) {
        e.preventDefault();
        const $panel = $(this).parents(".panel");
        const prefix = $panel.data("prefix");

        const [, current] = prefix.split("-");

        const $imagePanels = $("#product-images-section .panel");

        $imagePanels.removeClass("panel-selected").addClass("panel-default");

        $(".is-primary-image").replaceWith(function() {
            return $("<a>", {"class": "set-as-primary", "href": "#"}).text("Set as primary image");
        });

        $imagePanels.each(function(i) {
            $("#id_images-" + i + "-is_primary").prop("checked", false);
        });

        $(this).replaceWith(function() {
            return $("<span>", {"class": "is-primary-image"}).text("Primary image");
        });

        $panel.addClass("panel-selected");
        $("#id_images-" + current + "-is_primary").prop("checked", true);
    });

    $(".media-add-new-panel").on("click", function(e) {
        e.preventDefault();
        const panelCount = $("#" + $(this).data("target-panels") + " .panel").length;
        const $source = $("#placeholder-panel");
        const html = $source.html().replace(/__prefix__/g, panelCount - 1).replace(/__prefix_name__/g, panelCount);

        $(html).insertBefore($source);
        const targetId = $(this).data("target-id");
        const $totalFormsField = $("#" + targetId + "-TOTAL_FORMS");
        $totalFormsField.val(parseInt($totalFormsField.val()) + 1);
    });
});
