/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import m from "mithril";
import _ from "lodash";
import { handleResponseMessages } from "./util/remote";

const queue = [];
const queueCompleteCallbacks = [];
var queueStatusDiv = null;

function queueView() {
    var className = "empty";
    if (queue.length >= 0) {
        className = (
            _.every(queue, (file) => (file.status === "done" || file.status === "error")) ? "done" : "busy"
        );
    }

    return m("div.queue-view." + className, _.map(queue, (file) => {
        return m("div.queue-file." + file.status, [
            m("div.qf-name", file.name),
            m("div.qf-progress", {style: "width: " + (file.progress || 0) + "%"})
        ]);
    }));
}

function updateQueueView() {
    if (queueStatusDiv === null) {
        if (queue.length === 0) {
            return;  // Don't bother setting up the div if we're not doing anything actually
        }
        queueStatusDiv = document.createElement("div");
        queueStatusDiv.id = "queue-status-ctr";
        document.body.appendChild(queueStatusDiv);

        // Yes, we're throwing away the ctrl instance; we don't need it
        // and eslint would kvetch about it otherwise :)
        m.mount(queueStatusDiv, {view: queueView, controller: _.noop});
    }
    m.redraw();  // XXX: It would be nice if we could redraw only one Mithril view...
}

const updateQueueViewSoon = _.debounce(updateQueueView, 50);

function handleFileXhrComplete(xhr, file, error) {
    if (xhr.status >= 400) {
        error = true;
    }
    if (error) {
        file.status = "error";

    } else {
        file.status = "done";
        file.progress = 100;
    }
    setTimeout(processQueue, 50);  // Continue soon.
    var messageText = null;
    try {
        const responseJson = JSON.parse(xhr.responseText);
        if (responseJson) {
            if (responseJson.message) {
                messageText = responseJson.message;
            } else if (responseJson.error) {
                messageText = responseJson.error;
            }
        }
    } catch (e) {
        // invalid JSON? pffff.
        console.log(e); // eslint-disable-line
    }
    if (window.Messages) {
        if (error && !messageText) {
            messageText = gettext("Error! Unexpected error while uploading files.");
        }
        const response = {
            error: (error ? gettext("Error!") + " " + file.name + ": " + messageText : null),
            message: (!error ? messageText || gettext("Uploaded:") + " " + file.name : null)
        };
        handleResponseMessages(response);
    }
}

function beginUpload(file) {
    if (file.status !== "new") {  // Already uploaded? Huh.
        return false;
    }
    file.progress = 0;
    file.status = "uploading";

    const formData = new FormData();
    formData.append("file", file.nativeFile);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", file.url);
    xhr.setRequestHeader("X-CSRFToken", window.ShuupAdminConfig.csrf);
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) {
            // Ready state 4:
            // .. The data transfer has been completed or something went
            // .. wrong during the transfer (e.g. infinite redirects).
            // That's the only case we want to handle, so return otherwise.
            return;
        }
        handleFileXhrComplete(xhr, file, false);
        updateQueueViewSoon();
    };
    xhr.onerror = function() {
        handleFileXhrComplete(xhr, file, true);
        updateQueueViewSoon();
    };
    xhr.upload.onprogress = function(event) {
        if (event.lengthComputable) {
            file.progress = (event.loaded / event.total);
        } else {
            file.progress = file.progress + (100 - file.progress) / 2;
        }
        updateQueueViewSoon();
    };
    xhr.send(formData);
}

export function enqueue(uploadUrl, file) {
    queue.push({
        url: uploadUrl,
        name: file.name,
        nativeFile: file,
        status: "new",  // "new"/"uploading"/"error"/"done"
        progress: 0
    });
}

export function enqueueMultiple(uploadUrl, files) {
    _.each(files, (file) => {
        enqueue(uploadUrl, file);
    });
}

export function addQueueCompletionCallback(callback) {
    queueCompleteCallbacks.push(callback);
}

export function processQueue() {
    if (_.some(queue, (file) => file.status === "uploading")) {
        return;  // Don't allow uploading multiple files simultaneously though...
    }
    const nextFile = _.find(queue, (file) => (file.status === "new"));
    updateQueueViewSoon();
    if (nextFile) {
        beginUpload(nextFile);
    } else {
        while (queueCompleteCallbacks.length) {
            const cb = queueCompleteCallbacks.shift();
            cb();
        }
    }
}
