/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
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

    $(function() {
        $(".template-field-table :input").focus(function() {
            // Required for insertTemplateVariableExpression
            $lastFocusedTemplateInput = $(this);
        });
    });

    window.insertTemplateVariableExpression = insertTemplateVariableExpression;
}(window));
