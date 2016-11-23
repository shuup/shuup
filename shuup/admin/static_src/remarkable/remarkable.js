/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const marked = require("marked");
const m = require("mithril");

function escapeRegExp(str) {
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function wrapperModifyingFunction(preString, postString) {
    const preRegexp = new RegExp(escapeRegExp(preString) + "$");  // pre ends with marker?
    const postRegexp = new RegExp("^" + escapeRegExp(postString));  // post begins with marker
    return function(data) {
        if (preRegexp.test(data.pre)) {  // removing
            data.pre = data.pre.replace(preRegexp, "");
            data.post = data.post.replace(postRegexp, "");
            data.content = data.pre + data.mid + data.post;
            data.start -= preString.length;
            data.end -= postString.length;
        } else {
            data.content = data.pre + preString + data.mid + postString + data.post;
            data.start += preString.length;
            data.end += postString.length;
        }
        return data;
    };
}

function lineModifyingFunction(preString) {
    const preRegexp = new RegExp("^" + escapeRegExp(preString));  // pre begins with marker
    return function(data) {
        data.mid = data.mid.split("\n").map(function(line) {
            if (!line.length) {
                return line;
            }
            if (preRegexp.test(line)) {  // removing
                return line.replace(preRegexp, "");
            }
            return preString + line;
        }).join("\n");
        data.content = data.pre + data.mid + data.post;
        return data;
    };
}

function link(data) {
    data.content = data.pre + "[" + data.mid + "](http://)" + data.post;
    data.start = data.end = data.start + data.mid.length + 3;
    return data;
}

function controller() {
    const ctrl = this;
    ctrl.overlay = m.prop(null);
    ctrl.targetTextArea = m.prop(null);
    ctrl.content = m.prop("");
    ctrl.tools = m.prop([
        {title: "H1", action: lineModifyingFunction("# ")},
        {title: "H2", action: lineModifyingFunction("## ")},
        {title: "H3", action: lineModifyingFunction("### ")},
        "|",
        {icon: "bold", title: gettext("Bold"), action: wrapperModifyingFunction("**", "**")},
        {icon: "italic", title: gettext("Italic"), action: wrapperModifyingFunction("*", "*")},
        "|",
        {icon: "list", title: gettext("List"), action: lineModifyingFunction("* ")},
        {icon: "list-ol", title: gettext("Ordered list"), action: lineModifyingFunction("1. ")},
        "|",
        {icon: "link", title: gettext("Link"), action: link}
    ]);
    ctrl.setTargetTextArea = function(targetTextArea) {
        ctrl.targetTextArea(targetTextArea);
        ctrl.updateContent(targetTextArea.value);
        m.redraw();
    };
    ctrl.updateContent = function(content) {
        const textArea = ctrl.targetTextArea();
        ctrl.content(content);
        if (textArea) {
            textArea.value = content;
        }
    };
    ctrl.open = function() {
        ctrl.overlay().style.display = "block";
        document.body.classList.add("shuup-modal-open");
    };
    ctrl.destroy = function() {
        const ovl = ctrl.overlay();
        m.mount(ovl, null);  // self-destruct
        ovl.parentNode.removeChild(ovl);
        document.body.classList.remove("shuup-modal-open");
    };
}

function callTool(ctrl, toolAction) {
    return function() {
        const textArea = ctrl._editorTextArea;
        const data = {
            content: textArea.value,
            start: textArea.selectionStart,
            end: textArea.selectionEnd
        };
        data.pre = data.content.substring(0, data.start);
        data.mid = data.content.substring(data.start, data.end);
        data.post = data.content.substring(data.end, data.content.length);

        const rv = toolAction(data);
        textArea.focus();
        if (rv) {
            if (rv.content) {
                ctrl.updateContent(rv.content);
            }
            if (rv.start !== undefined) {
                ctrl._nextRenderSelection = {start: rv.start, end: rv.end || rv.start};
            }
        }
    };
}

function makeToolbar(ctrl) {
    var currentGroup = [];
    const toolGroups = [currentGroup];
    ctrl.tools().forEach(function(tool) {
        if (tool.separator || tool === "|") {
            toolGroups.push(currentGroup = []);
            return;
        }
        var className = "remarkable-tool btn btn-default";
        var buttonText = "";
        if (tool.icon) {
            className += " fa fa-" + tool.icon;
        } else {
            buttonText = tool.title;
        }
        currentGroup.push(m("button", {
            className: className,
            title: tool.title,
            onclick: callTool(ctrl, tool.action)
        }, buttonText));
    });
    return m("div.btn-toolbar", toolGroups.map(function(group) {
        return m("div.btn-group", group);
    }));
}

function view(ctrl) {
    return m("div.remarkable-wrap", [
        m("div.remarkable-container", [
            m("div.remarkable-header", [
                m("h2.pull-left", m("i.fa.fa-pencil"), gettext("Editor")),
                m("button.btn.btn-success.pull-right", {
                    title: "done",
                    onclick: ctrl.destroy
                }, m("i.fa.fa-check"), gettext("Done"))
            ]),
            m("div.remarkable-editor-panel", [
                m("div.remarkable-toolbar", makeToolbar(ctrl)),
                m("div.remarkable-editor", [
                    m("textarea.form-control", {
                        key: "editor",
                        oninput: m.withAttr("value", ctrl.updateContent),
                        value: ctrl.content(),
                        config: function(el) {
                            ctrl._editorTextArea = el;  // normal attr instead of mithril prop on purpose
                            if (ctrl._nextRenderSelection) {  // Fix-up the selection if any
                                const range = ctrl._nextRenderSelection;
                                el.setSelectionRange(range.start, range.end);
                                ctrl._nextRenderSelection = null;
                            }
                        }
                    })
                ])
            ]),
            m("div.remarkable-rendered", m.trust(marked(ctrl.content())))
        ])
    ]);
}

module.exports = function(targetTextArea) {
    const overlay = document.createElement("div");
    overlay.id = "remarkable-overlay";
    overlay.className = "remarkable-overlay";
    overlay.style.display = "none";
    document.body.appendChild(overlay);
    const ctrl = m.mount(overlay, {controller: controller, view: view});
    ctrl.overlay(overlay);
    ctrl.setTargetTextArea(targetTextArea);
    return ctrl;
};
