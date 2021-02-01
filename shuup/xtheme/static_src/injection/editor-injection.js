/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
// import styles
import "./editor-injection.less";

import domready from "../lib/domready";
import { stringify, mutateURL } from "../lib/qs";
import el from "../lib/el";
import ajax from "../lib/ajax";

var _sidebarDiv = null;
var _sidebarIframe = null;
var _sidebarToggler = null;

function getSidebarDiv() {
    if (_sidebarDiv === null) {
        _sidebarDiv = el("div", { id: "xt-edit-sidebar" }, [
            el("div", { id: "xt-edit-sidebar-container" },
                (_sidebarIframe = el("iframe", {
                    id: "xt-edit-sidebar-iframe"
                }))
            )
        ]);
        document.body.appendChild(_sidebarDiv);
    }
    return _sidebarDiv;
}

function getSidebarIframe() {
    getSidebarDiv();
    return _sidebarIframe;
}

function setPopup(visible) {
    const sidebarDiv = getSidebarDiv();
    if (visible === undefined) {
        sidebarDiv.classList.toggle("popout");
    } else {
        sidebarDiv.classList.toggle("popout", !!visible);
    }
}

function openPlaceholderEditor(domElement) {
    const layoutIdentifier = domElement.dataset.xtLayoutIdentifier;
    const layoutDataKey = domElement.dataset.xtLayoutDataKey;
    const placeholderName = domElement.dataset.xtPlaceholderName;
    const globalType = domElement.dataset.xtGlobalType;
    const contentTypeId = domElement.dataset.xtContentTypeId;
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
        "global_type": globalType,
        "layout_identifier": layoutIdentifier,
        "layout_data_key": layoutDataKey,
        // TODO: Hopefully we won't get any problems with too-long query strings (2048 is the maximum for IE):
        "default_config": defaultConfigJSON
    };
    getSidebarIframe().src = window.XthemeEditorConfig.editUrl + "?" + stringify(urlParams);
    setTimeout(() => {
        setPopup(true);
    }, 1); // Defer slide-out, because otherwise browsers coalesce the addClass (as it's done in the same JS "tick")
}

function addSnippetInjectionMarkup() {
    const nav = document.querySelector(".navbar-admin-tools .navbar-nav");
    if (!nav) return;  // No navigation no snippet in navigation either
    if (!document.querySelector(".xt-ph")) {
        // No placeholders in the DOM, so no need to show Inject button here.
        return;
    }
    const button = el("button", {
        "type": "button"
    }, gettext("Custom CSS/JS"));
    button.addEventListener("click", () => {
        window.open(window.XthemeEditorConfig.injectSnipperUrl, "_blank");
    });
    const li = el("li.xt-snippet-injection", [button]);
    nav.insertBefore(li, nav.firstChild);
}

function addEditToggleMarkup() {
    const hidden = (name, value) => el("input", { type: "hidden", name, value });
    const editing = (window.XthemeEditorConfig.edit);
    if (!document.querySelector(".xt-ph")) {
        // No placeholders in the DOM, so no need to show an Edit button here.
        return;
    }
    const li = el("li.xt-edit-toggle", [
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
    let nav = document.querySelector(".navbar-admin-tools .navbar-nav");
    if (!nav) return;  // No navigation no edit toggle in navigation either
    nav.insertBefore(li, nav.firstChild);
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
        url: mutateURL(location.href, { "_uncache_": +new Date() }),
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

function addCloseHandler() {
    document.addEventListener("keyup", (event) => {
        if (event.key === "Escape") {
            setPopup(false);
        }
    }, false);
}

domready(() => {
    window.addEventListener("message", handleMessage, false);
    addSnippetInjectionMarkup();
    addEditToggleMarkup();
    if (window.XthemeEditorConfig.edit) {
        addPhClickHandler();
        addCloseHandler();
    }
});


window.togglePopup = function(visible) {
    setPopup(visible);
};
