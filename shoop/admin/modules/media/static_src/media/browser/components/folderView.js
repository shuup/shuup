/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const button = require("./button");
const _ = require("lodash");
const emptyFolderView = require("./emptyFolderView");
const gridFileView = require("./gridFileView");
const listFileView = require("./listFileView");
const responsiveUploadHint = require("./responsiveUploadHint");
const {dropzoneConfig} = require("../util/dragDrop");
const images = require("./images");

export default function folderView(ctrl) {
    var folderData = ctrl.folderData();
    var viewModeGroup = m("div.btn-group.btn-group-sm.icons", [
        button(ctrl.viewMode, "grid", m("i.fa.fa-th"), "Grid"),
        button(ctrl.viewMode, "list", m("i.fa.fa-th-list"), "List")
    ]);
    var sortGroup = m("div.btn-group.btn-group-sm", [
        button(ctrl.sortMode, "+name", "A-Z"),
        button(ctrl.sortMode, "-name", "Z-A"),
        button(ctrl.sortMode, "+date", "Oldest first"),
        button(ctrl.sortMode, "-date", "Newest first"),
        button(ctrl.sortMode, "+size", "Smallest first"),
        button(ctrl.sortMode, "-size", "Largest first")
    ]);
    var toolbar = m("div.btn-toolbar", [viewModeGroup, sortGroup]);

    var sortSpec = /^([+-])(.+)$/.exec(ctrl.sortMode());
    var files = _.sortBy(folderData.files || [], sortSpec[2]);
    if (sortSpec[1] === "-") {
        files = files.reverse();
    }
    var folders = folderData.folders || [];
    var contents = null, uploadHint = null;
    if (folders.length === 0 && files.length === 0) {
        contents = emptyFolderView(ctrl, folderData);
        toolbar = null;
    } else {
        switch (ctrl.viewMode()) {
            case "grid":
                contents = gridFileView(ctrl, folders, files);
                break;
            case "list":
                contents = listFileView(ctrl, folders, files);
                break;
        }
        uploadHint = m("div.upload-hint", responsiveUploadHint);
    }
    var container = m("div.folder-contents.fd-zone", {
        "data-folder-id": folderData.id,
        config: dropzoneConfig(ctrl),
    }, [
        contents,
        uploadHint,
        m("div.upload-indicator", [
            m("div.image",
                m("img", {src: images.uploadIndicator})
            ),
            m("div.text", [
                m.trust("Drop your files here")
            ])
        ])
    ]);

    return m("div.folder-view", [toolbar, container]);
};
