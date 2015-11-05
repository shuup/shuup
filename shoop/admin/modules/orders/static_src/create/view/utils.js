/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";

export const LINE_TYPES = [
    {id: "product", name: "Product"},
    {id: "other", name: "Other"},
    {id: "text", name: "Text/Comment"}
];

export function selectBox(value, onchange, choices, valueGetter = "id", nameGetter = "name") {
    if (_.isString(valueGetter)) {
        valueGetter = _.partialRight(_.get, valueGetter);
    }
    if (_.isString(nameGetter)) {
        nameGetter = _.partialRight(_.get, nameGetter);
    }
    return m("select.form-control", {value, onchange}, choices.map(
        (obj) => m("option", {value: valueGetter(obj)}, nameGetter(obj))
    ));
}
