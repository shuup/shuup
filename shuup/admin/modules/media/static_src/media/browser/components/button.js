/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";

export default function(prop, value, label, title) {
    const active = (prop() == value);  // eslint-disable-line eqeqeq
    return m("button.btn.btn-default" + (active ? ".active" : ""), {
        type: "button",
        onclick: _.bind(prop, null, value),
        title: title
    }, label);
}
