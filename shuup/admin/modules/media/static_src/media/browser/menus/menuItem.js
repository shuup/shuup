/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const _ = require("lodash");
const m = require("mithril");
const menuManager = require("../util/menuManager");

export default function item(label, action, attrs = {}) {
    const tagBits = ["li"];
    if (attrs.disabled) {
        action = _.noop;
        tagBits.push("disabled");
    }
    return m(tagBits.join("."), m("a", {
        href: "#", onclick: (event) => {
            event.preventDefault();
            action();
            menuManager.close();
        }
    }, label));
}
