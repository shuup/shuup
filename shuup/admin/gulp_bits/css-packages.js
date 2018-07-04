/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
module.exports = {
    "vendor": {
        "entrypoint": "./node_modules/bootstrap-colorpicker/dist/css/bootstrap-colorpicker.css",
        "watches": []
    },
    "base": {
        "base": "./static_src/base",
        "entrypoint": "less/style.less",
        "watches": [
            "less/**/*.less"
        ]
    },
    "dashboard": {
        "base": "./static_src/dashboard",
        "entrypoint": "less/dashboard.less",
        "watches": [
            "less/**/*.less"
        ]
    },
    "home": {
        "base": "./static_src/home",
        "entrypoint": "less/home.less",
        "watches": [
            "less/**/*.less"
        ]
    },
    "media-browser": {
        "base": "./modules/media/static_src/media/browser",
        "entrypoint": "media-browser.less"
    },
    "select2": {
         "base": "./static_src/vendor/css",
         "entrypoint": "select2.css"
     },
     "wizard": {
         "base": "./static_src/wizard",
         "entrypoint": "less/wizard.less",
         "watches": [
             "less/**/*.less"
         ]
     }
};
