/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var mainBowerFiles = require("main-bower-files");
var path = require("path");
var gutil = require("gulp-util");

function bowerFiles(root) {
    try {
        return mainBowerFiles({
            paths: {
                bowerDirectory: path.normalize(path.join(root, "bower_components")),
                bowerJson: path.normalize(path.join(root, "bower.json"))
            },
            filter: /js$/,
            includeSelf: true
        });
    } catch (e) {
        gutil.log("Bower Files error (root=" + root + "):" + e);
        return [];
    }
}

module.exports = bowerFiles;
