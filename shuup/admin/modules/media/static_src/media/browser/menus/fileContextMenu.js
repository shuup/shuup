/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import menuItem from "./menuItem";
import * as fileActions from "../actions/fileActions";

export default function(controller, file) {
    return function() {
        return [
            menuItem(gettext("Rename file"), () => {
                fileActions.promptRenameFile(controller, file);
            }, {disabled: controller.isFileMenuDisabled("rename-file", file)}),
            menuItem(gettext("Delete file"), () => {
                fileActions.promptDeleteFile(controller, file);
            }, {disabled: controller.isFileMenuDisabled("delete-file", file)})
        ];
    };
}
