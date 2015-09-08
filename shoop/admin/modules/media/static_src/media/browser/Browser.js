/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var m = require("mithril");
var BrowserView = require("./BrowserView");
var FileUpload = require("./FileUpload");
const dragDrop = require("./util/dragDrop");
var controller = null;

export function init() {
    if (controller !== null) {
        return;
    }
    controller = m.mount(document.getElementById("BrowserView"), BrowserView);
    controller.navigateByHash();
    controller.reloadFolderTree();

    dragDrop.disableIntraPageDragDrop();
}

export function newFolder() {
    controller.promptCreateFolderHere();
}

export function setupUploadButton(element) {
    var input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.style.display = "none";
    input.addEventListener("change", function(event) {
        FileUpload.enqueueMultiple(controller.getUploadUrl(), event.target.files);
        FileUpload.addQueueCompletionCallback(() => { controller.reloadFolderContentsSoon(); });
        FileUpload.processQueue();
    });
    document.body.appendChild(input);
    element.addEventListener("click", function(event) {
        input.click();
        event.preventDefault();
    }, false);
}
