/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
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
import folderContextMenu from "./menus/folderContextMenu";
import getFolder from "./util/getFolder";
import * as remote from "./util/remote";

export function view(ctrl) {
    return m("div.container-fluid", [
        m("div.row", [
            m("div.col.page-inner-navigation.folder-tree", folderTree(ctrl)),
            m("div.col.page-content", m("div.content-block", [
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
        var id = ctrl.currentFolderId(),
            folder = getFolder(findPathToFolder(ctrl.rootFolder(), id), id);
        if (folder === undefined) {
            return true;
        }
        if (action in folder){
            return !folder[action];
        }

        return !folder["owner"]
    }

    ctrl.isFileMenuDisabled = function(action, file) {
        if (action in file){
            return !file[action];
        }
        return !file['owner'];
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
        var menuItems = folderContextMenu(ctrl)().filter(function( item ) {
            return item !== undefined;
        });

        if (menuItems.length > 0){
            $("#media-folder-edit-button").show();
        } else {
            $("#media-folder-edit-button").hide();
        }


        var id = ctrl.currentFolderId(),
            folder = getFolder(findPathToFolder(ctrl.rootFolder(), id), id);

        if (folder !== undefined && ("upload-media" in folder || folder["owner"])){
            $("#upload-button-wrapper").show();
        } else {
            $("#upload-button-wrapper").hide();
        }


        ctrl.currentFolderPath(findPathToFolder(ctrl.rootFolder(), currentFolderId));
    };
    ctrl.reloadFolderTree = function() {
        remote.get({"action": "folders"}).then(function(response) {
            if (response.rootFolder.id === 0 && !response.rootFolder.canSeeRoot) {
                // Hide the root folder if the user cannot access it.
                // This is only a visual thing to avoid showing the empty folder.
                // The view handles the actual permission checking and clears the whole file
                // QueyrSet of the root folder if the user is not allowed to access it.
                const currentFolder = response.rootFolder.children[0];
                ctrl.rootFolder(currentFolder || {});
                ctrl.currentFolderId(currentFolder ? currentFolder.id : null);
                ctrl.reloadFolderContents();
            } else {
                ctrl.rootFolder(response.rootFolder);
            }
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
