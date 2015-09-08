/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-bitwise */

const m = require("mithril");
const _ = require("lodash");

const folderTree = require("./components/folderTree");
const folderBreadcrumbs = require("./components/folderBreadcrumbs");
const folderView = require("./components/folderView");
const findPathToFolder = require("./util/findPathToFolder");


export function view(ctrl) {
    return m("div.container-fluid", [
        m("div.row", [
            m("div.col-md-3.page-inner-navigation.folder-tree", folderTree(ctrl)),
            m("div.col-md-9.page-content", m("div.content-block", [
                m("div.title", folderBreadcrumbs(ctrl)),
                m("div.content", folderView(ctrl))
            ]))
        ])
    ]);
}


export function controller() {
    var ctrl = this;
    ctrl.currentFolderId = m.prop(0);
    ctrl.currentFolderPath = m.prop([]);
    ctrl.rootFolder = m.prop({});
    ctrl.folderData = m.prop({});
    ctrl.viewMode = m.prop("grid");
    ctrl.sortMode = m.prop("+name");

    ctrl.setFolder = function(newFolderId) {
        ctrl.currentFolderId(0 | newFolderId);
        ctrl.currentFolderPath(findPathToFolder(ctrl.rootFolder(), newFolderId));
        ctrl.reloadFolderContents();
        location.hash = "#!id=" + newFolderId;
    };
    ctrl.promptCreateFolder = function(parentFolderId) {
        var name;
        if ((name = prompt("New folder name?"))) {
            m.request({
                method: "POST",
                url: location.pathname,
                data: {
                    "action": "new_folder",
                    "parent": parentFolderId,
                    "name": name
                },
                config: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
                }
            }).then(function() {
                ctrl.reloadFolderTree();
            });
        }
    };
    ctrl.promptCreateFolderHere = function() {
        return ctrl.promptCreateFolder(ctrl.currentFolderId());
    };
    ctrl.reloadFolderTree = function() {
        m.request({
            method: "GET",
            url: location.pathname,
            data: {"action": "folders"}
        }).then(function(response) {
            ctrl.rootFolder(response.rootFolder);
            ctrl.setFolder(ctrl.currentFolderId()); // Force reloading current folder too
        });
    };
    ctrl.reloadFolderContents = function() {
        var id = 0 | ctrl.currentFolderId();
        m.request({
            method: "GET",
            url: location.pathname,
            data: {"action": "folder", "id": id}
        }).then(function(response) {
            ctrl.folderData(response.folder || {});
        });
    };

    ctrl.getUploadUrl = function() {
        var uploadUrl = window.location.pathname;
        var folderId = ctrl.currentFolderId();
        return uploadUrl + "?action=upload&folder_id=" + folderId;
    };
    ctrl.reloadFolderContentsSoon = _.debounce(ctrl.reloadFolderContents, 1000);
}
