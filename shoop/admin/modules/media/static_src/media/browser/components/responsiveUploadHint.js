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

var NO_DND_UPLOAD_HINT = "Click the <strong>Upload</strong> button to upload files.";
var DND_UPLOAD_HINT = "<span>Drag and drop</span> files here<br> or click the <span>Upload</span> button.";

if (!FileUpload.supportsDnD) {
    DND_UPLOAD_HINT = NO_DND_UPLOAD_HINT;
}

const responsiveUploadHint = [
    m("div.visible-sm.visible-xs", m.trust(NO_DND_UPLOAD_HINT)),
    m("div.visible-md.visible-lg", m.trust(DND_UPLOAD_HINT))
];

export default responsiveUploadHint;
