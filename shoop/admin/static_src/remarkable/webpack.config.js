/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
module.exports = {
    entry: __dirname + "/remarkable",
    output: {
        libraryTarget: "var",
        library: "Remarkable"
    },
    externals: {
        "mithril": "m"
    }
};
