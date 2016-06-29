/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const _ = require("lodash");
const m = require("mithril");
const moment = require("moment");
const wrapFileLink = require("./wrapFileLink");
const folderLink = require("./folderLink");
const menuManager = require("../util/menuManager");
const fileContextMenu = require("../menus/fileContextMenu");

export default function(ctrl, folders, files) {
    const folderItems = _.map(folders, function(folder) {
        return m("tr", {key: "folder-" + folder.id}, [
            m("td", {colspan: 4}, [m("i.fa.fa-folder.folder-icon"), " ", folderLink(ctrl, folder)]),
        ]);
    });
    const fileItems = _.map(files, function(file) {
        return m("tr", {key: file.id}, [
            m("td", wrapFileLink(file)),
            m("td.text-right", file.size),
            m("td.text-right", moment(file.date).format()),
            m("td", {key: "filecog",
                onclick: (event) => {
                    menuManager.open(event.currentTarget, fileContextMenu(ctrl, file));
                    event.preventDefault();
                }
            }, m("i.fa.fa-cog"))
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
