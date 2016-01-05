/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
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
            "js/browse-widget.js",
            "js/side-nav.js",
            "js/content-blocks.js",
            "js/remarkable-field.js",
            "js/form-utils.js",
            "js/jquery.form-submission-attributes.polyfill.js",
            "js/datetimepicker.js"
        ]
    },
    "dashboard": {
        "es6": true,
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
        "es6": true,
        "base": "./static_src/picotable",
        "files": [
            "picotable.js"
        ]
    },
    "product-variation-variable-editor": {
        "base": root + "/modules/products/static_src",
        "es6": true,
        "files": [
            "product-variation-variable-editor.js"
        ]
    },
    "product": {
        "base": "./static_src/product",
        "es6": true,
        "files": [
            "edit_media.js"
        ]
    },
    "order-creator": {
        "webpack": root + "/modules/orders/static_src/create/webpack.config.js",
        "watch": [
            root + "/modules/orders/static_src/create/**/*.js"
        ]
    }
};
