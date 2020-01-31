/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import * as FileUpload from "../FileUpload";
import * as fileActions from "../actions/fileActions";

export const supportsDnD = (window.File && window.FileList && window.FormData);

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
            var data = null;
            try {
                data = JSON.parse(e.dataTransfer.getData("text"));
            } catch (exc) {
                // not JSON, I guess
            }
            if (data !== null) {
                if (data.fileId) {
                    fileActions.moveFile(ctrl, data.fileId, folderId);
                    return;
                }
            } else {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    FileUpload.enqueueMultiple(ctrl.getUploadUrl(folderId), files);
                    FileUpload.addQueueCompletionCallback(() => {
                        ctrl.reloadFolderContentsSoon();
                    });
                    FileUpload.processQueue();
                    return;
                }
            }
            alert("Error! You can only drop files here (from your computer or within the file manager).");
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
