/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");

export default function(ctrl, folder) {
    return m("a", {
        href: "#", onclick: function() {
            ctrl.setFolder(folder.id);
            return false;
        }
    }, folder.name);
}
