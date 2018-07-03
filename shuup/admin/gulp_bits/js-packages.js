/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var bowerFiles = require("./bower-files");
var root = require("path").resolve(__dirname + "/..");


module.exports = {
    "vendor": {
        "files": bowerFiles("./static_src/vendor").concat([
            "./node_modules/bootstrap-colorpicker/dist/js/bootstrap-colorpicker.js"
        ])
    },
    "base": {
        "base": "./static_src/base",
        "es6": true,
        "files": [
            "js/materialize.js",
            "js/main-menu.js",
            "js/search.js",
            "js/popover.js",
            "js/tooltip.js",
            "js/timesince.js",
            "js/messages.js",
            "js/browse-widget.js",
            "js/side-nav.js",
            "js/content-blocks.js",
            "js/form-utils.js",
            "js/jquery.form-submission-attributes.polyfill.js",
            "js/datetimepicker.js",
            "js/language-changer.js",
            "js/select.js",
            "js/tour.js",
            "js/imagelightbox.js",
            "js/drag-n-drop.js",
            "js/slugify.js",
            "js/dropzone.js",
            "js/quick_add_related_objects.js",
            "js/editor.js",
            "js/color-picker.js"
        ]
    },
    "contact-group": {
        "es6": true,
        "base": "./static_src/contact_group",
        "files": [
            "edit-members.js"
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
    },
    "wizard": {
        "base": "./static_src/wizard",
        "es6": true,
        "files": [
            "js/wizard.js"
        ]
    }
};
