/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */

window.setNextActionAndSubmit = function(formId, nextAction) {
    const $form = $("#" + formId);
    if(!$form.length) {
        return;
    }
    var $nextAction = $form.find("input[name=__next]");
    if(!$nextAction.length) {
        $nextAction = $("<input>", {
            type: "hidden",
            name: "__next"
        });
        $form.append($nextAction);
    }
    $nextAction.val(nextAction);
    $form.submit();
};

$(function() {
    const isMobile = !!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent));
    $(".multiselect").selectpicker({
        mobile: isMobile,
        style: "btn btn-select",
        title: "",
        selectedTextFormat: "count > 3",
        countSelectedText: "{0}/{1} selected"
    });
    const $dropdowns = $(".dropdown");
    // Add slideUp/slideDown animations to all bootstrap dropdowns
    $dropdowns.on("show.bs.dropdown", function() {
        $(this).find(".dropdown-menu").first().stop(true, true).slideDown(200, "easeInSine");
    }).on("hide.bs.dropdown", function() {
        $(this).find(".dropdown-menu").first().stop(true, true).slideUp(300, "easeOutSine");
    });
}());
