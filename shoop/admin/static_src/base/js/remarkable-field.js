/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    if(!window.Remarkable) return;
    $(".remarkable-field").each(function() {
        var textArea = this;
        var $container = $("<div class='remarkable-toggle'></div>");
        var $link = $("<button class='btn btn-info btn-sm' type='button'><i class='fa fa-expand'></i> Expand Editor</button>");
        $container.append($link);
        $link.click(function() {
            if($("#remarkable-overlay").length) return;
            Remarkable(textArea).open();
        });
        $(textArea).after($container);
    });
});

