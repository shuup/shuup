/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");

export function post(data) {
    return m.request({
        method: "POST",
        url: location.pathname,
        data: data,
        config: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
        }
    });
}

export function get(data) {
    return m.request({
        method: "GET",
        url: location.pathname,
        data: data
    });
}

export function handleResponseMessages(response) {
    const Messages = window.Messages;
    if (!Messages) {  // Messages module not available for whichever reason
        return;
    }
    const message = response.message;
    const error = response.error;
    if (error) {
        Messages.enqueue({tags: "error", text: error});
    }
    if (message) {
        Messages.enqueue({tags: "info", text: message});
    }
}
