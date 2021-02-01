/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function getModeFromSnippetType(type) {
    if (type === "inline_css") {
        return "css";
    } else if (type === "inline_js") {
        return "javascript";
    }
    return "htmlmixed";
}

window.addEventListener("load", () => {
    Array.from(document.getElementsByClassName("xtheme-code-editor-textarea")).forEach(el => {
        const $snippetType = $(el).closest("form").find("[name='snippet_type']");
        function createCodeMirror(mode) {
            window.ShuupCodeMirror.createCodeMirror(el, {
                mode: getModeFromSnippetType(mode)
            });
        }
        $snippetType.change((evt) => {
            createCodeMirror(evt.target.value);
        });

        createCodeMirror($snippetType.val());
    });
});
