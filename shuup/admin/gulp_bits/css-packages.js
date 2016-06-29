/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
module.exports = {
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
    "datatables": {
        "base": "./static_src/datatables",
        "entrypoint": "dataTables.bootstrap.less"
    },
    "media-browser": {
        "base": "./modules/media/static_src/media/browser",
        "entrypoint": "media-browser.less"
    },
    "select2": {
         "base": "./static_src/vendor/css",
         "entrypoint": "select2.css"
     }
};
