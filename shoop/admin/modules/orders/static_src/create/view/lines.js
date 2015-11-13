/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {addLine, deleteLine, retrieveProductData, setLineProperty} from "../actions";
import {selectBox, LINE_TYPES} from "./utils";
import BrowseAPI from "BrowseAPI";

export function renderOrderLines(store, lines) {
    return _(lines).map((line) => {
        var text = line.text, canEditPrice = true;
        const showPrice = (line.type !== "text");
        if (line.type === "product") {
            text = m("a", {
                href: "#",
                onclick: () => {
                    BrowseAPI.openBrowseWindow({
                        kind: "product",
                        onSelect: (obj) => {
                            store.dispatch(setLineProperty(line.id, "product", obj));
                            store.dispatch(retrieveProductData({id: obj.id, forLine: line.id}));
                        }
                    });
                }
            }, (line.product ? line.product.text : gettext("No product selected")));
            canEditPrice = (line.product && line.product.id);
        } else {
            text = m("input.form-control", {
                value: line.text,
                onchange: function () {
                    store.dispatch(setLineProperty(line.id, "text", this.value));
                }
            });
        }
        const priceCells = [
            m("td", m("input.form-control", {
                type: "number",
                min: 0,
                value: line.quantity,
                disabled: !canEditPrice,
                onchange: function () {
                    store.dispatch(setLineProperty(line.id, "quantity", this.value));
                }
            })),
            m("td", m("input.form-control", {
                type: "number",
                value: line.unitPrice,
                disabled: !canEditPrice,
                onchange: function () {
                    store.dispatch(setLineProperty(line.id, "unitPrice", this.value));
                }
            })),
            m("td.text-right", (line.quantity * line.unitPrice).toFixed(2))
        ];
        return m("tr", [
            m("td", selectBox(line.type, function () {
                store.dispatch(setLineProperty(line.id, "type", this.value));
            }, LINE_TYPES)),
            m("td", line.sku),
            m("td", {colspan: showPrice ? 1 : priceCells.length + 1}, text),
            (showPrice ? priceCells : null),
            m("td", m("button.btn.btn-xs.btn-danger", {
                onclick: function () {
                    store.dispatch(deleteLine(line.id));
                }
            }, m("i.fa.fa-trash")))
        ]);
    }).compact().value();
}

export function orderLinesView(store) {
    const {lines} = store.getState();
    return m("table.table.table-condensed.table-striped", [
        m("thead", [gettext("Type"), gettext("SKU"), gettext("Text"), gettext("Quantity"),
            gettext("Unit Price"), gettext("Total Price")].map((text) => m("th", text))),
        m("tbody",
            renderOrderLines(store, lines),
            m("tr", [
                m("td"),
                m("td", {colspan: 6}, m("a", {
                    href: "#", onclick: () => {
                        store.dispatch(addLine());
                    }
                }, gettext("Add new line..."))),
            ])
        )
    ]);
}
