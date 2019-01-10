/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-bitwise */
import menuItem from "./menuItem";
import * as folderActions from "../actions/folderActions";

export default function(controller) {
    return function() {
        const isRoot = (0 | controller.currentFolderId()) === 0;
        return [
            menuItem(gettext("New folder"), () => {
                folderActions.promptCreateFolderHere(controller);
            }, {disabled: controller.isMenuDisabled("new")}),
            menuItem(gettext("Rename folder"), () => {
                folderActions.promptRenameCurrentFolder(controller);
            }, {disabled: isRoot || controller.isMenuDisabled("rename")}),
            menuItem(gettext("Delete folder"), () => {
                folderActions.promptDeleteCurrentFolder(controller);
            }, {disabled: isRoot || controller.isMenuDisabled("delete")})
        ];
    };
}
