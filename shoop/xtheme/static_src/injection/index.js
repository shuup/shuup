/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
require("!style!css!autoprefixer!less!./style.less");
const domready = require("../lib/domready");
const qs = require("../lib/qs");
const el = require("../lib/el");
const ajax = require("../lib/ajax");

var _sidebarDiv = null;
var _sidebarIframe = null;

function getSidebarDiv() {
    if (_sidebarDiv === null) {
        _sidebarDiv = el("div", {id: "xt-edit-sidebar"}, [
            el("div.xt-sidebar-toggler", {
                $events: {
                    click: () => {
                        setSidebarVisibility();
                    }
                }
            }, [el("i.fa"), "Toggle Editor"]),
            (_sidebarIframe = el("iframe"))
        ]);
        document.body.appendChild(_sidebarDiv);
    }
    return _sidebarDiv;
}

function getSidebarIframe() {
    getSidebarDiv();
    return _sidebarIframe;
}

function setSidebarVisibility(visible) {
    const sidebarDiv = getSidebarDiv();
    if (visible === undefined) {
        sidebarDiv.classList.toggle("visible");
    } else {
        sidebarDiv.classList.toggle("visible", !!visible);
    }
}

function openPlaceholderEditor(domElement) {
    const placeholderName = domElement.dataset.xtPlaceholderName;
    if (!placeholderName) {
        return;
    }
    const defaultConfigElement = domElement.querySelector("script.xt-ph-default-layout");
    const defaultConfigJSON = (defaultConfigElement ? defaultConfigElement.innerHTML : null);
    const viewName = window.XthemeEditorConfig.viewName;
    const urlParams = {
        view: viewName,
        theme: window.XthemeEditorConfig.themeIdentifier,
        ph: placeholderName,

        // TODO: Hopefully we won't get any problems with too-long query strings (2048 is the maximum for IE):
        "default_config": defaultConfigJSON
    };
    getSidebarIframe().src = window.XthemeEditorConfig.editUrl + "?" + qs.stringify(urlParams);
    setTimeout(() => {
        setSidebarVisibility(true);
    }, 1); // Defer slide-out, because otherwise browsers coalesce the addClass (as it's done in the same JS "tick")
}

function addEditToggleMarkup() {
    const hidden = (name, value) => el("input", {type: "hidden", name, value});
    const editing = (window.XthemeEditorConfig.edit);
    if (!document.querySelector(".xt-ph")) {
        // No placeholders in the DOM, so no need to show an Edit button here.
        return;
    }
    const div = el("div.xt-edit-toggle", [
        el("form", {
            "action": window.XthemeEditorConfig.commandUrl,
            "method": "POST"
        }, [
            hidden("csrfmiddlewaretoken", window.XthemeEditorConfig.csrfToken),
            hidden("path", location.href),
            hidden("command", (editing ? "edit_off" : "edit_on")),
            el("button", {
                "type": "submit"
            }, (editing ? gettext("Exit Edit") : gettext("Edit Page")))
        ])
    ]);
    document.body.appendChild(div);
}

function handleMessage(event) {
    if (!window.XthemeEditorConfig.edit) {
        return;  // Not editing, ignore messages
    }
    if (event.origin !== location.origin) {
        return;  // Not our origin, can't be our message
    }
    const placeholder = event.data.reloadPlaceholder;
    if (!placeholder) {
        return; // Not our message
    }
    const oldPh = document.querySelector("#xt-ph-" + placeholder);
    if (!oldPh) {
        return;   // Not sure where to put output anyway
    }
    ajax({
        url: qs.mutateURL(location.href, {"_uncache_": +new Date()}),
        success: (text) => {
            const newDoc = document.implementation.createHTMLDocument();
            newDoc.body.innerHTML = text;
            const newPh = newDoc.querySelector("#xt-ph-" + placeholder);
            if (newPh) {
                oldPh.innerHTML = newPh.innerHTML;
            }
        }
    });
}

function addPhClickHandler() {
    document.addEventListener("click", (event) => {
        const classList = event.target.classList;
        if (classList && classList.contains("xt-ph")) {
            openPlaceholderEditor(event.target);
            event.preventDefault();
            event.stopPropagation();
            return false;
        }
    }, false);
}

domready(() => {
    window.addEventListener("message", handleMessage, false);
    addEditToggleMarkup();
    if (window.XthemeEditorConfig.edit) {
        addPhClickHandler();
    }
});
