/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const _ = require("lodash");
const wrapFileLink = require("./wrapFileLink");
const folderLink = require("./folderLink");
const {dropzoneConfig} = require("../util/dragDrop");
const images = require("./images");

export default function(ctrl, folders, files) {
    var folderItems = _.map(folders, function(folder) {
        return m("div.col-xs-6.col-md-4.col-lg-3.grid-folder.fd-zone", {
            key: "folder-" + folder.id,
            "data-folder-id": folder.id,
            config: dropzoneConfig(ctrl),
        }, [
            m("a.file-preview", {
                onclick: function() {
                    ctrl.setFolder(folder.id);
                    return false
                },
                href: "#"
            }, m("i.fa.fa-folder-open.folder-icon")),
            m("div.file-name", folderLink(ctrl, folder))
        ]);
    });
    var fileItems = _.map(files, function(file) {
        return m(
            "div.col-xs-6.col-md-4.col-lg-3.grid-file",
            {key: file.id},
            wrapFileLink(file, "a.file-preview", [,
                m("img.img-responsive", {src: file.thumbnail || images.defaultThumbnail}),
                m("div.file-name", file.name)
            ])
        );
    });
    return m("div.row", folderItems.concat(fileItems));
};
