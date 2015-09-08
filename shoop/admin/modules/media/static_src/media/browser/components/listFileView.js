/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const _ = require("lodash");
const m = require("mithril");
const moment = require("moment");
const wrapFileLink = require("./wrapFileLink");
const folderLink = require("./folderLink");


export default function(ctrl, folders, files) {
    var folderItems = _.map(folders, function(folder) {
        return m("tr", {key: "folder-" + folder.id}, [
            m("td", {colspan: 3}, [m("i.fa.fa-folder.folder-icon"), " ", folderLink(ctrl, folder)]),
        ]);
    });
    var fileItems = _.map(files, function(file) {
        return m("tr", {key: file.id}, [
            m("td", wrapFileLink(file)),
            m("td.text-right", file.size),
            m("td.text-right", moment(file.date).format())
        ]);
    });
    return m("div.table-responsive", [
        m("table.table.table-condensed.table-striped.table-bordered", [
            m("thead", m("tr", _.map(["Name", "Size", "Date"], function(title) {
                return m("th", title);
            }))),
            m("tbody", folderItems.concat(fileItems))
        ])
    ]);
};
