/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {addLine, deleteLine, retrieveProductData, setLineProperty, updateTotals, setQuickAddProduct, clearQuickAddProduct, setAutoAdd, addProduct} from "../actions";
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


var Select2 = {
    view: function(ctrl, attrs) {
        return m("select", {
            config: Select2.config(attrs)
        });
    },
    config: function(ctrl) {
        return function(element, isInitialized) {
            if(typeof jQuery !== "undefined" && typeof jQuery.fn.select2 !== "undefined") {
                let $el = $(element);
                if (!isInitialized) {
                    activateSelect($el, ctrl.model, ctrl.attrs).on("change", () => {
                        // note: data is only populated when an element is actually clicked or enter is pressed
                        const data = $el.select2("data");
                        ctrl.onchange(data);
                        if(ctrl.focus()){
                            // close it first to clear the search box...
                            $el.select2("close");
                            $el.select2("open");
                        }
                    });
                } else {
                    // this doesn't actually set the value for ajax autoadd
                    $el.val(ctrl.value().id).trigger("change");
                    // trigger select2 dropdown repositioning
                    $(window).scroll();
                }

            } else {
                alert(gettext("Missing JavaScript dependencies detected"));
            }
        };
    }
};


var ProductQuickSelect = {
    view: function(ctrl, attrs) {
        const {store} = attrs;

        return m.component(Select2, {
            model: "shuup.product",
            attrs: {
                ajax: {
                    processResults: function (data) {
                        const {quickAdd} = store.getState();
                        const results = {
                            results: $.map(data.results, function (item) {
                                return {text: item.name, id: item.id};
                            })
                        };
                        if(quickAdd.autoAdd && results.results.length === 1) {
                            store.dispatch(setQuickAddProduct(results.results[0]));
                            store.dispatch(addProduct(results.results[0]));
                            store.dispatch(clearQuickAddProduct());
                            return {results: []};
                        }
                        return results;
                    }
                }
            },
            value: () => store.getState().quickAdd.product,
            focus: () => store.getState().quickAdd.autoAdd && store.getState().quickAdd.product.id,
            onchange: (product) => {
                const {quickAdd} = store.getState();
                if(product && product.length) {
                    if(quickAdd.autoAdd) {
                        store.dispatch(addProduct(product[0]));
                    } else {
                        store.dispatch(setQuickAddProduct(product[0]));
                    }
                }
            }
        });
    }
};

export function orderLinesView(store, isCreating) {
    const {lines, shop, quickAdd} = store.getState();
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
                        if (quickAdd.product.id){
                            store.dispatch(retrieveProductData(
                                {id: quickAdd.product.id, forLine: _.last(store.getState().lines).id}
                            ));
                        }
                    }
                }, m("i.fa.fa-plus"), " " + gettext("Add new line"))
            ),
            m("div.col-sm-6", [
                m("fieldset", [
                    m("legend", gettext("Quick add product line")),
                    m.component(ProductQuickSelect, {store: store}),
                    m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
                        disabled: isCreating,
                        onclick: () => {
                            if (quickAdd.product.id){
                                store.dispatch(addProduct(quickAdd.product));
                                store.dispatch(clearQuickAddProduct());
                            }
                        }
                    }, m("i.fa.fa-plus")),
                    m("button.btn.text-success" + (isCreating ? ".disabled": ""), {
                        disabled: isCreating,
                        onclick: () => {
                            store.dispatch(clearQuickAddProduct());
                        }
                    }, m("i.fa.fa-trash")),
                    m("span.help-block", gettext("Search product by name, SKU, or barcode and press button to add product line.")),
                    m("input", {
                        type: "checkbox",
                        checked: quickAdd.autoAdd,
                        onchange: function() {
                            store.dispatch(clearQuickAddProduct());
                            store.dispatch(setAutoAdd(this.checked));
                        }
                    }),
                    m("span.quick-add-check-text", " " + gettext("Automatically add selected product")),
                ])
            ]),
        ]),
    ]);
}
