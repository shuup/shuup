/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-shadow,eqeqeq */
const _ = require("lodash");

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
