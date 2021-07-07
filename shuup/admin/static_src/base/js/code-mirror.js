/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
if (window.ShuupCodeMirror) {
    window.ShuupCodeMirror.editors = {}; // expose all created editors

    window.ShuupCodeMirror.createCodeMirror = (target, attrs) => {
        // it is already there, destroy it first
        if (window.ShuupCodeMirror.editors[target.id]) {
            window.ShuupCodeMirror.editors[target.id].toTextArea();
        }
        const baseAttrs = {
            mode: "htmlmixed",
            matchBrackets: true,
            matchTags: true,
            autoCloseBrackets: true,
            autoCloseTags: true,
            lineNumbers: true,
            ...attrs,
        };
        window.ShuupCodeMirror.editors[target.id] = window.ShuupCodeMirror.fromTextArea(target, baseAttrs);

        // Refresh code mirror objects on tab-clicks to active the editor
        $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function () {
            this.refresh();
        }.bind(window.ShuupCodeMirror.editors[target.id]));

        if ($(target).hasClass("code-editor-with-preview")) {
            // For code mirror objects with preview option sync editor
            // content to HTML prview iframe which should be available
            // through preview container
            window.ShuupCodeMirror.editors[target.id].on("change", function (editor) {
                $(target)
                    .closest(".code-editor-with-preview-container")
                    .find("iframe.html-preview")
                    .attr("srcdoc", editor.getValue())
            })
        }

        return window.ShuupCodeMirror.editors[target.id];
    };

    Array.from(document.getElementsByClassName("code-editor-textarea")).forEach(el => {
        window.ShuupCodeMirror.createCodeMirror(el);
    });
}
