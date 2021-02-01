/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";
import offset from "./offset";

var currentMenuParent = null;
var currentMenuComponent = null;
var fallbackParentCoords = null;
var menuContainer = null;
var currentMenuOpenTs = 0;
const widthMargin = 20;

export function isMenuVisible() {
    return (currentMenuParent !== null && menuContainer !== null);
}

function reattachNow() {
    if (!isMenuVisible()) {
        return;
    }
    const parentCoords = offset(currentMenuParent) || fallbackParentCoords;
    if (parentCoords === null) {
        return;
    }
    const viewWidth = window.innerWidth;
    var x = parentCoords.left;
    const y = parentCoords.top + parentCoords.height + 5;
    const menuOffset = offset(menuContainer);
    const menuWidth = menuOffset ? menuOffset.width : 0;  // ah well
    if (viewWidth && x + menuWidth > viewWidth - widthMargin) {
        x = x + parentCoords.width - menuWidth;
    }

    _.assign(menuContainer.style, {
        "display": "block",
        "left": `${x}px`,
        "top": `${y}px`,
        "position": "absolute",
        "zIndex": 9000
    });
}

const reattachSoon = _.debounce(reattachNow, 20);

function menuView(view) {
    return function() {
        var items = null;
        if (_.isArray(view)) {  // It's already an array of items, fine
            items = view;
        }
        if (_.isFunction(view)) {  // It's a function returning something..?
            items = view();
        }
        if (_.isArray(items)) {  // If it was items, wrap them.
            return m(
                "ul.dropdown-menu",
                {style: "display: block; float: none; position: static; top: 0"},
                items
            );
        }
        return items;
    };
}

function initializeMenuContainer() {
    if (menuContainer === null) {
        menuContainer = document.createElement("div");
        document.body.appendChild(menuContainer);
        window.addEventListener("resize", reattachSoon, false);
        window.addEventListener("scroll", reattachSoon, false);
        document.body.addEventListener("click", function(event) {
            if (!isMenuVisible()) {
                return;
            }
            if ((+new Date() - currentMenuOpenTs) < 200) {
                return;  // Ignore mis-taps within a short time of the opening click
            }
            var node = event.target;
            do {
                if (node === menuContainer) {
                    return false;
                }
            } while ((node = node.parentElement));
            close();
        }, false);

        //setInterval(reattachSoon, 100);
    }
    return menuContainer;
}

export function open(parent, view) {
    if (currentMenuParent === parent) {
        close();
        return;
    }
    if (parent) {
        initializeMenuContainer();
    }
    currentMenuParent = parent;
    currentMenuComponent = (view ? {view: menuView(view), controller: _.noop} : null);
    currentMenuOpenTs = +new Date();
    if (menuContainer) {
        m.mount(menuContainer, currentMenuComponent);
        fallbackParentCoords = parent ? offset(parent) : null;
        if (view) {
            reattachNow();
            setTimeout(reattachSoon, 100);
        }
    }
}

export function close() {
    open(null, null);
}
