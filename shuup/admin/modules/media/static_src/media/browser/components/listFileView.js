/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import _ from "lodash";
import m from "mithril";
import moment from "moment";
import wrapFileLink from "./wrapFileLink";
import folderLink from "./folderLink";
import fileContextMenu from "../menus/fileContextMenu";
import * as menuManager from "../util/menuManager";

export default function(ctrl, folders, files) {
    const folderItems = _.map(folders, function(folder) {
        return m("tr", {key: "folder-" + folder.id}, [
            m("td", {colspan: 4}, [m("i.fa.fa-folder.folder-icon"), " ", folderLink(ctrl, folder)]),
        ]);
    });
    const fileItems = _.map(files, function(file) {
        var editOptionsAvailable = fileContextMenu(ctrl, file)().filter(function( item ) {
            return item !== undefined;
         });

        return m("tr", {key: file.id}, [
            m("td", wrapFileLink(file)),
            m("td.text-right", file.size),
            m("td.text-right", moment(file.date).format()),
            editOptionsAvailable.length > 0 ? m("td", {key: "filecog",
                onclick: (event) => {
                    menuManager.open(event.currentTarget, fileContextMenu(ctrl, file));
                    event.preventDefault();
                }
            }, m("i.fa.fa-cog")) : null
        ]);
    });
    return m("div.table-responsive", [
        m("table.table.table-condensed.table-striped.table-bordered", [
            m("thead", m("tr", _.map([gettext("Name"), gettext("Size"), gettext("Date"), gettext("Edit")], function(title) {
                return m("th", title);
            }))),
            m("tbody", folderItems.concat(fileItems))
        ])
    ]);
}
