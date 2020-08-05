/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
if (window.ShuupCodeMirror) {
    window.ShuupCodeMirror.editors = {}; // expose all created editors

    window.ShuupCodeMirror.createCodeMirror = (target, attrs) => {
        // it is already there, destroy it first
        if (window.ShuupCodeMirror.editors[target]) {
            window.ShuupCodeMirror.editors[target].toTextArea();
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
        window.ShuupCodeMirror.editors[target] = window.ShuupCodeMirror.fromTextArea(target, baseAttrs);
        return window.ShuupCodeMirror.editors[target];
    };

    Array.from(document.getElementsByClassName("code-editor-textarea")).forEach(el => {
        window.ShuupCodeMirror.createCodeMirror(el);
    });
}
