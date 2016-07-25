/**
 * This file is part of Shuup.
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
        var editCell = null;
        const showPrice = (line.type !== "text");
        if (line.type === "product") {
            text = m("a", {
                    href: "#",
                    onclick: (e) => {
                        e.preventDefault();
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
                }, (line.product ? [
                    line.product.text, m("br"),
                    m("small", "(" + line.sku + ")"), m("br"),
                    m("small", gettext("Logical Count") + ": " + line.logicalCount), m("br"),
                    m("small", gettext("Physical Count") + ": " + line.physicalCount)
                ] : gettext("Select product"))
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
        if (line.type === "product" && line.product ){
            editCell = m("div.line-cell.edit",
                m("button.btn.btn-sm.text-info", {
                    onclick: function(e) {
                        e.preventDefault();
                        window.open(line.product.url, "_blank");
                    }
                }, m("i.fa.fa-edit")));
        }
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
                editCell,
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

var select2 = {
    clear: function() {
        if (select2.element) {
            select2.element.select2("val", null);
        }
    },
    view: function(ctrl, attrs) {
        return m("select", {
            config: select2.config(attrs), "data-model": "shuup.product"});
    },
    config: function(ctrl) {
        return function(element, isInitialized) {
            if(typeof jQuery !== "undefined" && typeof jQuery.fn.select2 !== "undefined") {
                var el = $(element);
                select2.element = el;
                if (!isInitialized) {
                    // This is needed to reset prop when going back from confirmation view
                    productQuickSelect.currentProduct(null);
                    el.select2()
                        .on("change", function() {
                            ctrl.onchange($(this).val());
                        });
                }
            } else {
                alert(gettext("Missing JavaScript dependencies detected"));
            }
        };
    }
};

var productQuickSelect = {
    clearSelection: function() {
        productQuickSelect.currentProduct(null);
        select2.clear();
    },
    currentProduct: m.prop(),
    changeProduct: function(id) {
        productQuickSelect.currentProduct(id);
    },
    view: function() {
        return m.component(select2, {
            onchange: this.changeProduct,
        });
    }
};

export function orderLinesView(store, isCreating) {
    const {lines, shop} = store.getState();
    // This is needed to make select work when going back from confirmation view
    store.dispatch(updateTotals(store.getState));
    return m("div", [
        m("p", gettext("If your product prices vary based on customer, you might want to select customer first.")),
        m("p", interpolate(gettext("All prices are in %s currency."), [shop.selected.currency])),
        m(
            "p",
            shop.selected.pricesIncludeTaxes ? gettext("All prices include taxes.") : gettext("Taxes not included.")
        ),
        m("div.list-group", renderOrderLines(store, shop.selected, lines)),
        m("hr"),
        m("div.row", [
            m("div.col-sm-6",
                m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
                    disabled: isCreating,
                    onclick: () => {
                        store.dispatch(addLine());
                        var productId = productQuickSelect.currentProduct();
                        if (productId){
                            store.dispatch(retrieveProductData(
                                {id: productId, forLine: _.last(store.getState().lines).id}
                            ));
                        }
                    }
                }, m("i.fa.fa-plus"), " " + gettext("Add new line"))
            ),
            m("div.col-sm-6", [
                m("fieldset", [
                    m("legend", gettext("Quick add product line")),
                    productQuickSelect,
                    m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
                        disabled: isCreating,
                        onclick: () => {
                            store.dispatch(addLine());
                            var productId = productQuickSelect.currentProduct();
                            if (productId){
                                store.dispatch(retrieveProductData(
                                    {id: productId, forLine: _.last(store.getState().lines).id}
                                ));
                            }
                            productQuickSelect.clearSelection();
                        }
                    }, m("i.fa.fa-plus")),
                    m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
                        disabled: isCreating,
                        onclick: productQuickSelect.clearSelection,
                    }, m("i.fa.fa-trash")),
                    m("span.help-block", gettext("Search product by name, SKU, or barcode and press button to add product line.")),
                ])
            ]),
        ]),
    ]);
}
