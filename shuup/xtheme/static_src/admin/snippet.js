/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import CodeMirror from "codemirror";

import "codemirror/mode/javascript/javascript";
import "codemirror/mode/css/css";
import "codemirror/mode/htmlmixed/htmlmixed";
import "codemirror/addon/edit/closebrackets";
import "codemirror/addon/edit/closetag";
import "codemirror/addon/edit/matchbrackets";
import "codemirror/addon/edit/matchtags";

window.CodeMirror = CodeMirror;
CodeMirror.editors = {};    // expose all creted editors

function getModeFromSnippetType(type) {
    if (type === "inline_css") {
        return "css";
    } else if (type === "inline_js") {
        return "javascript";
    }
    return "htmlmixed";
}

window.addEventListener("load", () => {
    Array.from(document.getElementsByClassName("snippet-editor-textarea")).forEach((el) => {
        let codeMirror = null;
        const $snippetType = $(el).closest("form").find("[name='snippet_type']");
        function createCodeMirror(mode) {
            codeMirror = CodeMirror.fromTextArea(el, {
                mode: getModeFromSnippetType(mode),
                matchBrackets: true,
                matchTags: true,
                autoCloseBrackets: true,
                autoCloseTags: true,
                lineNumbers: true
            });
            CodeMirror.editors[el.getAttribute("id")] = codeMirror;
        }
        $snippetType.change((evt) => {
            if (codeMirror) {
                codeMirror.toTextArea();
            }
            createCodeMirror(evt.target.value);
        });

        createCodeMirror($snippetType.val());
    });
});
