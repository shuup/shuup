/**
* This file is part of Shoop.
*
* Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
*
* This source code is licensed under the AGPLv3 license found in the
* LICENSE file in the root directory of this source tree.
 */
window.MediaBrowser = (function() {
    var BrowserView = require("./BrowserView");
    var FileUpload = require("./FileUpload");
    var controller = null;
    var init = function() {
        controller = m.mount(document.getElementById("BrowserView"), BrowserView);
        var currentIdMatch = /#!id=(\d+)/.exec(location.hash);
        if(currentIdMatch) {
            controller.setFolder(currentIdMatch[1]);
        } else {
            controller.setFolder(0);
        }
        controller.reloadFolderTree();
    };
    var newFolder = function() {
        controller.promptCreateFolderHere();
    };
    var setupUploadButton = function(element) {
        var input = document.createElement("input");
        input.type = "file";
        input.className = "invisible-file-input";
        input.addEventListener("change", function(event) {
            FileUpload.uploadNativeFiles(
                controller.getUploadUrl(),
                event.target.files,
                controller.reloadFolderContentsSoon
            );
        });
        element.style.width = element.offsetWidth + "px";
        element.style.height = element.offsetHeight + "px";
        element.appendChild(input);
    };
    return {
        init: init,
        newFolder: newFolder,
        setupUploadButton: setupUploadButton,
    };
}());
