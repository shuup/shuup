/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function($) {
    "use strict";

    const allowedButtons = "input[type=\"submit\"], input[type=\"image\"], button:not([type]), button[type=\"submit\"]";
    const formAttributes = ["action", "method", "enctype", "target", "novalidate"];

    $.fn.formSubmissionAttributes = function() {
        //based on https://github.com/mattberkowitz/Form-Submission-Attributes-Polyfill

        this.each(function() {
            const $form = $(this);
            var $inputs = $form.find(allowedButtons);
            const formId = $form.attr("id");

            if (formId) {
                // find buttons that are tied to this form and add them to $inputs
                var buttons = $("input[form=\"" + formId + "\"],button[form=\"" + formId + "\"]");
                buttons = buttons.filter(allowedButtons);
                $inputs = $inputs.add(buttons);
            }

            //backup originals
            $.each(formAttributes, function(idx, attr) {
                $form.data("o" + attr, $form.attr(attr));
            });

            $inputs.on("click", function() {
                const $this = $(this);
                $.each(formAttributes, function(idx, attr) {
                    const value = $this.is("[form" + attr + "]") ? $this.attr("form" + attr) : $form.data("o" + attr);
                    $form.attr(attr, value);
                });
            });
        });
    };

    if (window.navigator.userAgent.indexOf("MSIE ") > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./))
    {
        $(document).on("click", "[type=submit][form]", function(event) {
            event.preventDefault();
            const formId = $(this).attr("form");
            const $f = $("#" + formId);
            $f.formSubmissionAttributes();
            $f.submit();
        });
    }
}(jQuery));
