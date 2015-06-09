/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var fd = require("filedrop");
var queue = [];

function processQueue(done) {
    if (queue.length === 0) return;
    var spec = queue.shift();
    var file = spec.file;
    var url = spec.url;
    file.event("xhrSetup", function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
    });
    file.event("done", function(xhr) {
        var data = JSON.parse(xhr.responseText);
        if (data.error) alert(data.error);
        if(done) done(file, queue.length);
        processQueue(done);
    });
    file.sendTo(url);
}


function createMessageShowingDoneFunction(done) {
    return function(file, queueLength) {
        if(window.Messages) Messages.enqueue({tags: "success", text: "Uploaded: " + file.name});
        done();
    };
}

/**
 * Mithril.js configurator for a Filedrop drop zone
 * @param ctrl Controller supporting `.getUploadUrl()`
 */
function dropzoneConfig(ctrl) {
    return function(element, isInitialized) {
        if (isInitialized) return;
        var zone = element._filedrop_ = new fd.FileDrop(element, {input: false, multiple: true});


        zone.event('send', function(files) {
            var url = ctrl.getUploadUrl();
            files.each(function(file) {
                queue.push({url: url, file: file});
            });
            processQueue(createMessageShowingDoneFunction(done));
        });
    };
}

/**
 * Upload native HTML 5 files
 * @param uploadUrl
 * @param nativeFiles Array[File]
 * @param done Function
 */
function uploadNativeFiles(uploadUrl, nativeFiles, done) {
    for(var i = 0; i < nativeFiles.length; i++) {
        var nativeFile = nativeFiles[i];
        queue.push({url: uploadUrl, file: new fd.File(nativeFile)});
    }
    processQueue(createMessageShowingDoneFunction(done));
}

module.exports = {
    dropzoneConfig: dropzoneConfig,
    uploadNativeFiles: uploadNativeFiles,
};
