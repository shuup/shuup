/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.Messages = (function Messages(document) {
    const queue = [];
    let container = null;
    let timeOutForHide = null;
    let timeOutForClear = null;

    function createContainer() {
        if (!container) {
            container = document.createElement("div");
            container.id = "message-container";
            document.body.appendChild(container);
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
          timeOutForHide = setTimeout(() => {
              container.classList.remove("visible");
              container.classList.add("clear");
              timeOutForClear = setTimeout(clear, 1000);
          }, 2000)
        }
    }
    function clear() {
        container.classList.remove("clear");
        while (container && container.firstChild) {
            container.removeChild(container.firstChild);
        }
    }
    function renderMessage(message) {
        const messageDiv = document.createElement("div");
        let tags = message.tags || [];
        if (_.isString(tags)) {
            tags = tags.split(" ");
        }
        messageDiv.className = "message " + tags.join(" ");
        const textSpan = document.createElement("span");
        textSpan.className = "content";
        const textNode = document.createTextNode(message.text || "no text");
        textSpan.appendChild(textNode);

        const dismissIcon = document.createElement("span");
        dismissIcon.className = "dimiss-icon";
        const statusIcon = document.createElement("span");
        statusIcon.className = "status";

        messageDiv.addEventListener("click", () => clear());

        messageDiv.appendChild(statusIcon);
        messageDiv.appendChild(textSpan);
        messageDiv.appendChild(dismissIcon);
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

        if (timeOutForHide !== null) {
            // Reset the timeout for hiding the messages when a new message is added.
            clearTimeout(timeOutForHide);
            timeOutForHide = null;
        }
        if (timeOutForClear !== null) {
            // Immediately clear the already hidden messages a when new one is added.
            clearTimeout(timeOutForClear);
            timeOutForClear = null;
            clear();
        }

        while (queue.length > 0) {
            container.appendChild(renderMessage(queue.shift()));
        }
        _.defer(show);
        hide();
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
