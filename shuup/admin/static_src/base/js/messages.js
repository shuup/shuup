/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.Messages = (function Messages(document) {
    const queue = [];
    var container = null;
    function createContainer() {
        if (!container) {
            container = document.createElement("div");
            container.id = "message-container";
            document.body.appendChild(container);
            document.addEventListener("click", hideOnClickOut, false);
        }
    }
    function show() {
        if (container) {
            container.classList.remove("clear");
            container.classList.add("visible");
        }
    }
    function hide() {
        if (container) {
            container.classList.remove("visible");
            container.classList.add("clear");
            setTimeout(clear, 2000);
        }
    }
    function clear() {
        container.classList.remove("clear");
        while (container && container.firstChild) {
            container.removeChild(container.firstChild);
        }
    }
    function hideOnClickOut(event) {
        var node = event.target;
        while (node) {
            if (node.id === "message-container") {
                return;
            }
            node = node.parentNode;
        }
        hide();
    }
    function renderMessage(message) {
        const messageDiv = document.createElement("div");
        var tags = message.tags || [];
        if (_.isString(tags)) {
            tags = tags.split(" ");
        }
        messageDiv.className = "message " + tags.join(" ");
        const textSpan = document.createElement("span");
        const textNode = document.createTextNode(message.text || "no text");
        textSpan.appendChild(textNode);
        messageDiv.appendChild(textSpan);
        return messageDiv;
    }
    function flush() {
        if (!queue.length) {
            return;
        }
        if (!document.body) {  // Try again soon
            return setTimeout(flush, 50);
        }
        createContainer();
        while (queue.length > 0) {
            container.appendChild(renderMessage(queue.shift()));
        }
        _.defer(show);
    }
    const deferredFlush = _.debounce(flush, 50);
    function enqueue(message) {
        queue.push(message);
        deferredFlush();
    }

    return {
        enqueue: enqueue,
        hide: hide
    };
}(window.document));
