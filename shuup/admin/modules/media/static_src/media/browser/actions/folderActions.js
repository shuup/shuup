/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import _ from "lodash";
import * as remote from "../util/remote";

export function promptCreateFolder(controller, parentFolderId) {
    const name = prompt(gettext("New folder name?"));
    if (!name) {  // Cancelled? :(
        return;
    }
    remote.post({action: "new_folder", parent: parentFolderId, name}).then(function(response) {
        remote.handleResponseMessages(response);
        const newCurrentFolder = 0 | response.folder.id;  // eslint-disable-line no-bitwise
        controller.setFolder(newCurrentFolder);
        controller.reloadFolderTree();
        controller.reloadFolderContents();
    });
}

export function promptCreateFolderHere(controller) {
    return promptCreateFolder(controller, controller.currentFolderId());
}

export function promptRenameCurrentFolder(controller) {
    const {id, name} = controller.folderData();
    const newName = _.trim(prompt(gettext("New folder name?"), name) || "");
    if (newName && name !== newName) {
        remote.post({action: "rename_folder", id, name: newName}).then(function(response) {
            remote.handleResponseMessages(response);
            controller.reloadFolderTree();
            controller.reloadFolderContents();
        });
    }
}

export function promptDeleteCurrentFolder(controller) {
    const {id, name} = controller.folderData();
    if (confirm(interpolate(gettext("Are you sure you want to delete the %s folder?"), [name]))) {
        remote.post({action: "delete_folder", id}).then(function(response) {
            remote.handleResponseMessages(response);
            const newCurrentFolder = 0 | response.newFolderId;  // eslint-disable-line no-bitwise
            controller.setFolder(newCurrentFolder);
            controller.reloadFolderTree();
            controller.reloadFolderContents();
        });
    }
}

export function editAccessCurrentFolder(controller) {
    const {id, name} = controller.folderData();
    remote.get({action: "edit_url", id}).then(function(response) {
        window.location = response['url'];
    });
}
