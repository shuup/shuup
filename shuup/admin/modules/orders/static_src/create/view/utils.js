/**
 * This file is part of Shuup.
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

export function selectBox(value, onchange, choices, valueGetter = "id", nameGetter = "name", name = "") {
    if (_.isString(valueGetter)) {
        valueGetter = _.partialRight(_.get, valueGetter);
    }
    if (_.isString(nameGetter)) {
        nameGetter = _.partialRight(_.get, nameGetter);
    }
    return m("select.form-control", {value, onchange, name}, choices.map(
        (obj) => m("option", {value: valueGetter(obj)}, nameGetter(obj))
    ));
}

export function contentBlock(icon, title, view, header = "h2") {
    return m("div.content-block",
        m("div.title",
            m(header + ".block-title", m(icon), " " + title),
            m("a.toggle-contents", m("i.fa.fa-chevron-right"))
        ),
        m("div.content-wrap.collapse",
            m("div.content", view)
        )
    );
}

export function infoRow(header, value, klass) {
    if(value && value !== ""){
        return m("div", [
            m("dt", header),
            m("dd" + (klass? klass : ""), value)
        ]);
    }
}

export function table({columns, data=[], tableClass="", emptyMsg=gettext("No records found.")}) {
    return m("table", {class: "table " + tableClass},
        m("thead",
            m("tr", columns.map(col => m("th", col.label)))
        ),
        m("tbody",
            (data.length > 0?
            data.map(row => m("tr", columns.map(col => m("td", row[col.key])))):
            m("tr", m("td[colspan='" + columns.length + "'].text-center", m("i", emptyMsg))))
        )
    );
}

export function modal({show=false, sizeClass="", title, body, footer, close}) {
    if(show){
        $("body").append("<div class='modal-backdrop in'></div>").addClass("modal-open");
    } else {
        $("body").removeClass("modal-open").find(".modal-backdrop").remove();
    }

    return (
        m("div.modal" + (show? " show": " hidden"),
            m("div.modal-dialog", {class: sizeClass},
                m("div.modal-content",
                    m("div.modal-header",
                        m("button.close",
                            m("span", {
                                onclick: () => close()
                            }, m.trust("&times;"))
                        ),
                        title
                    ),
                    m("div.modal-body", body),
                    m("div.modal-footer", footer)
                )
            )
        )
    );
}
