(function($) {
    "use strict";

    var allowedButtons = "input[type=\"submit\"], input[type=\"image\"], button:not([type]), button[type=\"submit\"]";
    var formAttributes = ["action", "method", "enctype", "target", "novalidate"];

    $.fn.formSubmissionAttributes = function () {
        //based on https://github.com/mattberkowitz/Form-Submission-Attributes-Polyfill

        this.each(function () {
            var $form = $(this);
            var $inputs = $form.find(allowedButtons);
            var formId = $form.attr("id");

            if (formId) {
                // find buttons that are tied to this form and add them to $inputs
                var buttons = $("input[form=\"" + formId + "\"],button[form=\"" + formId + "\"]");
                buttons = buttons.filter(allowedButtons);
                $inputs = $inputs.add(buttons);
            }

            //backup originals
            $.each(formAttributes, function (idx, attr) {
                $form.data("o" + attr, $form.attr(attr));
            });

            $inputs.on("click", function (e) {
                var $this = $(this);
                $.each(formAttributes, function(idx, attr) {
                    var value = $this.is("[form" + attr + "]") ? $this.attr("form" + attr) : $form.data("o" + attr);
                    $form.attr(attr, value);
                });
            });
        });
    };

    if(window.navigator.userAgent.indexOf("MSIE ") > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./))
    {
        $(document).on("click", "[type=submit][form]", function(event) {
            event.preventDefault();
            var formId = $(this).attr("form");
            var $f = $("#" + formId);
            $f.formSubmissionAttributes();
            $f.submit();
        });
    }
}(jQuery));
