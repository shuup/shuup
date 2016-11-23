/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const responsiveUploadHint = require("./responsiveUploadHint");

export default function(ctrl, folder) {  // eslint-disable-line no-unused-vars
    return m("div.empty-folder", [
        m("div.empty-image",
            m("img", {src: require("!url!./file-icons.svg")})
        ),
        m("div.empty-text", responsiveUploadHint)
    ]);
}
