/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var bowerFiles = require("./bower-files");
var root = require("path").resolve(__dirname + "/..");
module.exports = {
    "vendor": {
        "files": bowerFiles("./static_src/vendor")
    },
    "base": {
        "base": "./static_src/base",
        "es6": true,
        "files": [
            "js/materialize.js",
            "js/main-menu.js",
            "js/search.js",
            "js/tooltip.js",
            "js/timesince.js",
            "js/messages.js",
            "js/media-widget.js",
            "js/dropdown-animation.js",
            "js/side-nav.js",
            "js/content-blocks.js",
            "js/custom-selects.js",
            "js/remarkable-field.js",
            "js/form-utils.js",
        ]
    },
    "dashboard": {
        "files": bowerFiles("./static_src/dashboard")
    },
    "media-browser": {
        "webpack": root + "/modules/media/webpack.config.js",
        "watch": [
            "./modules/media/static_src/media/**/*.js"
        ]
    },
    "remarkable": {
        "webpack": root + "/static_src/remarkable/webpack.config.js",
        "watch": [
            "./static_src/remarkable/*.js"
        ]
    },
    "picotable": {
        "base": "./static_src/picotable",
        "files": [
            "picotable.js",
        ]
    }
};
