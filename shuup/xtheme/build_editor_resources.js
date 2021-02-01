/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const { getParcelBuildCommand, runBuildCommands } = require("shuup-static-build-tools");

runBuildCommands([
    getParcelBuildCommand({
        cacheDir: "xtheme",
        outputDir: "static/xtheme/",
        entryFile: "static_src/editor/editor.less"
    }),
    getParcelBuildCommand({
        cacheDir: "xtheme",
        outputDir: "static/xtheme/",
        entryFile: "static_src/editor/editor.js"
    }),
    getParcelBuildCommand({
        cacheDir: "xtheme",
        outputDir: "static/xtheme/",
        entryFile: "static_src/editor/vendor.js"
    })
]);
