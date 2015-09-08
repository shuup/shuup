/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const FileUpload = require("../FileUpload");

export var supportsDnD = (window.File && window.FileList && window.FormData);

function ignoreEvent(e) {
    e = e || event;
    e.stopPropagation();
    e.preventDefault();
}

export function dropzoneConfig(ctrl) {
    if (!ctrl) {
        throw new Error("ctrl required");
    }
    return function(element, isInitialized) {
        if (isInitialized) {
            return;
        }
        element.addEventListener("dragover", function(e) {
            const folderId = element.dataset.folderId;
            if (!folderId) {
                return;
            }
            ignoreEvent(e);
            e.dataTransfer.dropEffect = "copy";
            element.classList.add("over");
            m.redraw.strategy("none");
        }, false);
        element.addEventListener("dragenter", function(e) {
            ignoreEvent(e);
            m.redraw.strategy("none");
        }, false);
        element.addEventListener("dragleave", function(e) {
            ignoreEvent(e);
            element.classList.remove("over");
        }, false);
        element.addEventListener("drop", function(e) {
            const folderId = element.dataset.folderId;
            ignoreEvent(e);
            element.classList.remove("over");
            const files = e.dataTransfer.files;
            if (files.length === 0) {
                alert("You can only drop files here.");
                return;
            }
            FileUpload.enqueueMultiple(ctrl.getUploadUrl(folderId), files);
            FileUpload.addQueueCompletionCallback(() => {
                ctrl.reloadFolderContentsSoon();
            });
            FileUpload.processQueue();
        });
    };
}

export function disableIntraPageDragDrop() {
    document.addEventListener("dragstart", ignoreEvent, false);
    document.addEventListener("dragover", function(e) {
        e.dataTransfer.dropEffect = "none";
        ignoreEvent(e);
    }, false);
    document.addEventListener("drop", ignoreEvent, false);
}
