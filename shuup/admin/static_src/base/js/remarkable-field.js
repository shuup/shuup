/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    var EXPAND_EDITOR_MARKUP = (
        "<button class='btn btn-info btn-sm' type='button'>" +
        "<i class='fa fa-expand'></i> " + gettext("Expand Editor") +
        "</button>"
    );
    const remarkable = window.Remarkable;
    if (!remarkable) {
        return;
    }
    $(".remarkable-field").each(function() {
        const textArea = this;
        const $container = $("<div class='remarkable-toggle'></div>");
        const $link = $(EXPAND_EDITOR_MARKUP);
        $container.append($link);
        $link.click(function() {
            if ($("#remarkable-overlay").length) {
                return;
            }
            remarkable(textArea).open();
        });
        $(textArea).after($container);
    });
});

