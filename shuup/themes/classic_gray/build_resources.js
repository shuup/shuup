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
        cacheDir: "classic_gray",
        outputDir: "static/shuup/classic_gray/pink",
        entryFile: "static_src/pink/style.css"
    }),
    getParcelBuildCommand({
        cacheDir: "classic_gray",
        outputDir: "static/shuup/classic_gray/blue",
        entryFile: "static_src/blue/style.css"
    })
]);
