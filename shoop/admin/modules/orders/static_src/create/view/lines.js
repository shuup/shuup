/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {addLine, deleteLine, retrieveProductData, setLineProperty, updateTotals} from "../actions";
import {LINE_TYPES, selectBox} from "./utils";
import BrowseAPI from "BrowseAPI";

function renderNumberCell(store, line, value, fieldId, canEditPrice, min=null) {
    return m("input.form-control", {
            type: "number",
            step: line.step,
            min: min != null ? min : "",
            value: value,
            disabled: !canEditPrice,
            onchange: function () {
                store.dispatch(setLineProperty(line.id, fieldId, this.value));
                if (fieldId === "quantity" && line.product) {
                    store.dispatch(retrieveProductData(
                        {id: line.product.id, forLine: line.id, quantity: this.value}
                    ));
                }
                store.dispatch(updateTotals(store.getState));
            }
    });
}

export function renderOrderLines(store, shop, lines) {
    return _(lines).map((line) => {
        var text = line.text, canEditPrice = true;
        const showPrice = (line.type !== "text");
        if (line.type === "product") {
            text = m("a", {
                    href: "#",
                    onclick: () => {
                        BrowseAPI.openBrowseWindow({
                            kind: "product",
                            filter: {"shop": shop.id},
                            onSelect: (obj) => {
                                store.dispatch(setLineProperty(line.id, "product", obj));
                                store.dispatch(retrieveProductData(
                                    {id: obj.id, forLine: line.id, quantity: line.quantity}
                                ));
                            }
                        });
                    }
                }, (line.product ?
                    [line.product.text, m("br"), m("small", "(" + line.sku + ")")] : gettext("Select product"))
            );
            canEditPrice = (line.product && line.product.id);
        } else {
            text = [
                m("label", gettext("Text/Comment")),
                m("input.form-control", {
                    type: "text",
                    value: line.text,
                    maxlength: 256,
                    onchange: function () {
                        store.dispatch(setLineProperty(line.id, "text", this.value));
                    }
                })
            ];
        }
        const priceCells = [
            m("div.line-cell", [
                m("label", gettext("Qty")),
                renderNumberCell(store, line, line.quantity, "quantity", canEditPrice, 0)
            ]),
            m("div.line-cell", [
                m("label", gettext("Unit Price")),
                renderNumberCell(store, line, line.unitPrice, "unitPrice", canEditPrice)
            ]),
            m("div.line-cell", [
                m("label", gettext("Total Price")),
                renderNumberCell(store, line, line.total, "total", canEditPrice)
            ])
        ];
        const productPriceCells = [
            m("div.line-cell", [
                m("label", gettext("Qty")),
                renderNumberCell(store, line, line.quantity, "quantity", canEditPrice, 0)
            ]),
            m("div.line-cell", [
                m("label", gettext("Base Unit Price")),
                renderNumberCell(store, line, line.baseUnitPrice, "baseUnitPrice", false)
            ]),
            m("div.line-cell", [
                m("label", gettext("Discounted Unit Price")),
                renderNumberCell(store, line, line.unitPrice, "unitPrice", canEditPrice)
            ]),
            m("div.line-cell", [
                m("label", gettext("Discount Percent")),
                renderNumberCell(store, line, line.discountPercent, "discountPercent", canEditPrice)
            ]),
            m("div.line-cell", [
                m("label", gettext("Total Discount Amount")),
                renderNumberCell(store, line, line.discountAmount, "discountAmount", canEditPrice)
            ]),
            m("div.line-cell", [
                m("label", gettext("Line Total")),
                renderNumberCell(store, line, line.total, "total", canEditPrice)
            ])
        ];
        return m("div.list-group-item", [
            m("div.cells", [
                m("div.line-cell.line-type-select", [
                    m("label", gettext("Orderline type")),
                    selectBox(line.type, function () {
                        store.dispatch(setLineProperty(line.id, "type", this.value));
                        store.dispatch(updateTotals(store.getState));
                    }, LINE_TYPES)
                ]),
                m("div.line-cell", text),
                (showPrice ? (line.type === "product" ? productPriceCells : priceCells) : null),
                m("div.line-cell.delete",
                    m("button.btn.btn-sm.text-danger", {
                        onclick: function () {
                            store.dispatch(deleteLine(line.id));
                            store.dispatch(updateTotals(store.getState));
                        }
                    }, m("i.fa.fa-trash")))
            ]),
            line.errors ? m("p.text-danger", line.errors) : null
        ]);
    }).compact().value();
}

export function orderLinesView(store, isCreating) {
    const {lines, shop} = store.getState();
    return m("div", [
        m("p", gettext("If your product prices vary based on customers you might wan't to select customer first.")),
        m("p", gettext(gettext("All prices is in ") + shop.selected.currency + " currency.")),
        m(
            "p",
            shop.selected.pricesIncludeTaxes ? gettext("All prices include taxes.") : gettext("Taxes is not included.")
        ),
        m("div.list-group", renderOrderLines(store, shop.selected, lines)),
        m("hr"),
        m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
            disabled: isCreating,
            onclick: () => {
                if(!isCreating) {
                    store.dispatch(addLine());
                }
            }
        }, m("i.fa.fa-plus"), " " + gettext("Add new line"))
    ]);
}
