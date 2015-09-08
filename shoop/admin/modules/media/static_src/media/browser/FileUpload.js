/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var fd = require("filedrop");
export var supportsDnD = (window.File && window.FileList && window.FileReader);

const queue = [];


function processQueue(done) {
    if (queue.length === 0) {
        return;
    }
    var spec = queue.shift();
    var file = spec.file;
    var url = spec.url;
    file.event("xhrSetup", function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
    });
    file.event("done", function(xhr) {
        var data = JSON.parse(xhr.responseText);
        if (data.error) {
            alert(data.error);
        }
        if(done) {
            done(file, queue.length);
        }
        processQueue(done);
    });
    file.sendTo(url);
}


function createMessageShowingDoneFunction(done) {
    return function(file, queueLength) {  // eslint-disable-line no-unused-vars
        if(window.Messages) {
            window.Messages.enqueue({tags: "success", text: "Uploaded: " + file.name});
        }
        done();
    };
}

/**
 * Upload native HTML 5 files
 * @param uploadUrl
 * @param nativeFiles Array[File]
 * @param done Function
 */
export function uploadNativeFiles(uploadUrl, nativeFiles, done) {
    /*for(var i = 0; i < nativeFiles.length; i++) {
        var nativeFile = nativeFiles[i];
        queue.push({url: uploadUrl, file: new fd.File(nativeFile)});
    }*/
    processQueue(createMessageShowingDoneFunction(done));
}

export function dropzoneConfig(ctrl) {
    // TODO: Reimplement me...
}
