/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import _ from "lodash";
import m from "mithril";
import * as menuManager from "../util/menuManager";

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
