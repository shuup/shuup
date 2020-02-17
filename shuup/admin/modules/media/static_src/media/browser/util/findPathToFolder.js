/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-shadow,eqeqeq */
import _ from "lodash";

export default function(rootFolder, folderId) {
    var pathToFolder = null;

    function walk(folder, folderPath) {
        if (folder.id == folderId) {
            pathToFolder = folderPath.concat([folder]);
            return;
        }
        folderPath = [].concat(folderPath).concat([folder]);
        _.each(folder.children, function(folder) {
            if (!pathToFolder) {
                walk(folder, folderPath);
            }
        });
    }

    walk(rootFolder, []);
    return pathToFolder || [];
}
