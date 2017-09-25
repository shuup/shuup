/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

// This file is not transpiled, so prefer-const isn't valid
/* eslint-disable prefer-const */
(function() {
    var $lastFocusedTemplateInput = null;

    function insertTemplateVariableExpression(variableName) {
        if (!$lastFocusedTemplateInput) {
            return false;
        }
        var variableExpression = "{{ " + variableName + " }}";
        var caretPos = $lastFocusedTemplateInput.prop("selectionStart");
        var text = $lastFocusedTemplateInput.val();
        if (_.isNumber(caretPos)) {
            text = text.substring(0, caretPos) + variableExpression + text.substring(caretPos);
        } else {
            text = (text + variableExpression);
        }
        $lastFocusedTemplateInput.val(text);
        $lastFocusedTemplateInput.focus();
    }

    function refreshTabPanes() {
        $(".tab-pane").hide();
        var currentActiveHref = $("#main-tabs").find("li.active a").attr("href");
        if (currentActiveHref) {
            var tabId = currentActiveHref.split("#", 2)[1];
            $("#" + tabId).show();
        }
    }

    $(function() {
        $("#main-tabs").find("a").click(function() {
            var $link = $(this);
            $(".nav-tabs li").removeClass("active");
            $link.parents(".nav-tabs li").addClass("active");
            refreshTabPanes();
            return false;
        });
        refreshTabPanes();
        $(".template-field-table :input").focus(function() {
            // Required for insertTemplateVariableExpression
            $lastFocusedTemplateInput = $(this);
        });
    });

    window.insertTemplateVariableExpression = insertTemplateVariableExpression;
}(window));
