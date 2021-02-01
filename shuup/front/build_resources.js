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
        cacheDir: "front",
        outputDir: "static/shuup/front/js",
        entryFile: "static_src/js/vendor.js"
    }),
    getParcelBuildCommand({
        cacheDir: "front",
        outputDir: "static/shuup/front/js",
        outputFileName: "scripts",
        entryFile: "static_src/js/index.js"
    }),
    getParcelBuildCommand({
        cacheDir: "front",
        outputDir: "static/shuup/front/css",
        entryFile: "static_src/less/style.css"
    })
]);
