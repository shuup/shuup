/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-bitwise */

import m from "mithril";
import  _  from "lodash";

import folderTree from "./components/folderTree";
import folderBreadcrumbs from "./components/folderBreadcrumbs";
import folderView from "./components/folderView";
import findPathToFolder from "./util/findPathToFolder";
import * as remote from "./util/remote";

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

export function controller(config={}) {
    const ctrl = this;
    ctrl.currentFolderId = m.prop(null);
    ctrl.currentFolderPath = m.prop([]);
    ctrl.rootFolder = m.prop({});
    ctrl.folderData = m.prop({});
    ctrl.viewMode = m.prop("grid");
    ctrl.sortMode = m.prop("+name");

    ctrl.isMenuDisabled = function(action) {
        return (config.disabledMenus || []).indexOf(action) >= 0;
    }
    ctrl.setFolder = function(newFolderId) {
        newFolderId = 0 | newFolderId;
        if (ctrl.currentFolderId() === newFolderId) {
            return;  // Nothing to do, don't cause trouble
        }
        ctrl.currentFolderId(0 | newFolderId);
        ctrl._refreshCurrentFolderPath();
        ctrl.reloadFolderContents();
        location.hash = "#!id=" + newFolderId;
    };
    ctrl._refreshCurrentFolderPath = function() {
        const currentFolderId = ctrl.currentFolderId();
        if (currentFolderId === null) {
            return;  // Nothing loaded yet; defer to later
        }
        ctrl.currentFolderPath(findPathToFolder(ctrl.rootFolder(), currentFolderId));
    };
    ctrl.reloadFolderTree = function() {
        remote.get({"action": "folders"}).then(function(response) {
            ctrl.rootFolder(response.rootFolder);
            ctrl._refreshCurrentFolderPath();
        });
    };
    ctrl.reloadFolderContents = function() {
        const id = 0 | ctrl.currentFolderId();
        remote.get({"action": "folder", id, filter: config.filter}).then(function(response) {
            remote.handleResponseMessages(response);
            ctrl.folderData(response.folder || {});
        });
    };

    ctrl.getUploadUrl = function(folderId) {
        const uploadUrl = window.location.pathname;
        folderId = folderId === undefined ? ctrl.currentFolderId() : folderId;
        return uploadUrl + "?action=upload&folder_id=" + folderId;
    };
    ctrl.reloadFolderContentsSoon = _.debounce(ctrl.reloadFolderContents, 1000);

    ctrl.navigateByHash = function() {
        const currentIdMatch = /#!id=(\d+)/.exec(location.hash);
        const newFolderId = currentIdMatch ? currentIdMatch[1] : 0;
        ctrl.setFolder(newFolderId);
    };

    window.addEventListener("hashchange", () => {
        ctrl.navigateByHash();
    }, false);
}
