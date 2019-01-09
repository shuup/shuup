/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function processAttrs(element, attrs) {
    for (var key in attrs) {
        if (!attrs.hasOwnProperty(key)) {
            continue;
        }
        if (key === "$events") {
            const eventHash = attrs[key];
            for (var eventName in eventHash) {
                if (!eventHash.hasOwnProperty(eventName)) {
                    continue;
                }
                element.addEventListener(eventName, eventHash[eventName], false);
            }
            continue;
        }
        element[key] = attrs[key];
    }
}

function processChildren(element, children) {
    if (children && !Array.isArray(children)) {
        children = [children];
    }
    (children || []).forEach((child) => {
        if (!child) {
            return;
        }
        if (typeof child === "string") {
            child = document.createTextNode(child);
        }
        element.appendChild(child);
    });
}

/**
 * Generate a HTML element.
 * For instance, el("div.foo", {id: "y"}, ["Hello", "Hello"]) would generate
 * a div with the outerHTML `<div id="y" class="foo">HelloHello</div>`.
 *
 * @param selector Tag + CSS classes, separated with full-stops.
 * @param attrs Optional hash of attributes to assign on the new element.
 * @param children Optional array of children for the node.
 * @returns {HTMLElement}
 */
export default function el(selector, attrs, children) {
    const [tag, ...classes] = selector.split(".");
    const element = document.createElement(tag);
    classes.forEach((cls) => {
        element.classList.add(cls);
    });
    if (Array.isArray(attrs)) {
        children = attrs;
        attrs = {};
    }
    processAttrs(element, attrs);
    processChildren(element, children);
    return element;
}
