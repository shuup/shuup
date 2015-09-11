/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-bitwise */
const folderActions = require("../actions/folderActions");
const menuItem = require("./menuItem");


export default function(controller) {
    return function() {
        const isRoot = (0 | controller.currentFolderId()) === 0;
        return [
            menuItem("New folder...", () => {
                folderActions.promptCreateFolderHere(controller);
            }),
            menuItem("Rename folder...", () => {
                folderActions.promptRenameCurrentFolder(controller);
            }, {disabled: isRoot}),
            menuItem("Delete folder", () => {
                folderActions.promptDeleteCurrentFolder(controller);
            }, {disabled: isRoot})
        ];
    };
}
