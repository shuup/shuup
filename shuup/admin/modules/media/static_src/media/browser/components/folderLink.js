/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";

export default function(ctrl, folder) {
    return m("a", {
        href: "#", onclick: function() {
            ctrl.setFolder(folder.id);
            return false;
        }
    }, folder.name);
}
