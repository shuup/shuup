/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";
import wrapFileLink from "./wrapFileLink";
import folderLink from "./folderLink";
import { dropzoneConfig } from "../util/dragDrop";
import * as images from "./images";
import * as menuManager from "../util/menuManager";
import fileContextMenu from "../menus/fileContextMenu";

export default function(ctrl, folders, files) {
    const folderItems = _.map(folders, function(folder) {
        return m("div.grid-folder.fd-zone", {
            key: "folder-" + folder.id,
            "data-folder-id": folder.id,
            config: dropzoneConfig(ctrl),
        }, [
            m("a.file-preview", {
                onclick: function() {
                    ctrl.setFolder(folder.id);
                    return false;
                },
                href: "#"
            }, m("i.fa.fa-folder-open.folder-icon")),
            m("div.file-name", folderLink(ctrl, folder))
        ]);
    });
    const fileItems = _.map(files, function(file) {
        var editOptionsAvailable = fileContextMenu(ctrl, file)().filter(function( item ) {
            return item !== undefined;
        });

        return m(
            "div.grid-file",
            {
                key: file.id,
                draggable: true,
                ondragstart: (event) => {
                    event.stopPropagation();
                    event.dataTransfer.effectAllowed = "copyMove";
                    event.dataTransfer.setData("text", JSON.stringify({"fileId": file.id}));
                    try {
                        const dragIcon = document.createElement("img");
                        dragIcon.src = file.thumbnail || images.defaultThumbnail;
                        dragIcon.width = 100;
                        event.dataTransfer.setDragImage(dragIcon, 0, 0);
                    } catch (e) {
                        // This isn't a problem
                    }
                }
            },
            editOptionsAvailable.length > 0 ? m("button.file-cog-btn.btn.btn-xs.btn-default", {
                key: "filecog",
                onclick: (event) => {
                    menuManager.open(event.currentTarget, fileContextMenu(ctrl, file));
                    event.preventDefault();
                }
            }, m("i.fa.fa-cog")) : null,
            wrapFileLink(file, "a.file-preview", [
                m("div.preview-img-wrap", [
                    m("img.img-responsive", {src: file.thumbnail || images.defaultThumbnail}),
                ]),
                m("div.file-name", file.name)
            ])
        );
    });
    return m("div.custom-browser-row", folderItems.concat(fileItems));
}
