/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";

export const LINE_TYPES = [
    {id: "product", name: gettext("Product")},
    {id: "other", name: gettext("Other")},
    {id: "text", name: gettext("Text/Comment")}
];

export const ADDRESS_FIELDS = [
    {key: "name", label: gettext("Name"), "required": true},
    {key: "tax_number", label: gettext("Tax number"), "required": false},
    {key: "phone", label: gettext("Phone"), "required": false},
    {key: "email", label: gettext("Email"), "required": false},
    {key: "street", label: gettext("Street"), "required": true},
    {key: "street2", label: gettext("Street (2)"), "required": false},
    {key: "postal_code", label: gettext("ZIP / Postal code"), "required": false},
    {key: "city", label: gettext("City"), "required": true},
    {key: "region", label: gettext("Region"), "required": false},
    {key: "country", label: gettext("Country"), "required": true}
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

export function contentBlock(icon, title, view) {
    return m("div.content-block",
        m("div.title",
            m("h2.block-title", m(icon), " " + title),
            m("a.toggle-contents", m("i.fa.fa-chevron-right"))
        ),
        m("div.content-wrap.collapse",
            m("div.content", view)
        )
    );
}
