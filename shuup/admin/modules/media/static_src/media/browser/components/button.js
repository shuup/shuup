/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const _ = require("lodash");

export default function(prop, value, label, title) {
    const active = (prop() == value);  // eslint-disable-line eqeqeq
    return m("button.btn.btn-default" + (active ? ".active" : ""), {
        type: "button",
        onclick: _.bind(prop, null, value),
        title: title
    }, label);
}

