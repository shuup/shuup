/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const BrowseAPI = window.BrowseAPI;
import {
    addLine,
    deleteLine,
    retrieveProductData,
    setLineProperty,
    updateTotals,
    setQuickAddProduct,
    clearQuickAddProduct,
    setAutoAdd,
    addProduct
} from "../actions";
import {
    LINE_TYPES,
    selectBox,
    Select2,
    HelpPopover
} from "./utils";
import ensureNumericValue from "../utils/numbers";

function renderNumberCell(store, line, value, fieldId, canEditPrice, asInteger = false, min = null) {
    return m("input.form-control", {
            name: fieldId,
            type: "number",
            step: line.step,
            min: min !== null ? min : "",
            value: ensureNumericValue(value, min, asInteger),
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
                        window.BrowseAPI.openBrowseWindow({
                            kind: "product",
                            filter: {"shop": shop.id},
                            onSelect: (obj) => {
                                store.dispatch(setLineProperty(line.id, "product", obj));
                                store.dispatch(retrieveProductData({
                                    id: obj.id,
                                    forLine: line.id,
                                    quantity: line.quantity
                                }));
                            }
                        });
                    }
                }, (line.product ? [
                    line.product.text, m("br"),
                    m("small", "(" + line.sku + ")"), m("br"),
                    m("small", line.supplier.name), m("br"),
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
                }),
                m.component(HelpPopover, {
                    title: gettext("Text/Comment"),
                    content: gettext("Enter a comment or text note about the order. This could be anything " +
                        "from special order requests to special shipping needs.")
                })
            ];
        }
        const priceCells = [
            m("div.line-cell", [
                m("label", gettext("Qty")),
                renderNumberCell(store, line, line.quantity, "quantity", canEditPrice, true, 0),
                m.component(HelpPopover, {
                    title: gettext("Quantity"),
                    content: gettext("Enter the number of units of the product ordered.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Unit Price")),
                renderNumberCell(store, line, line.unitPrice, "unitPrice", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Unit Price"),
                    content: gettext("Enter the regular base price for a single unit of the product. If an " +
                        "existing product is selected, the price is already determined in product settings. " +
                        "Total price will be automatically calculated.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Total Price")),
                renderNumberCell(store, line, line.total, "total", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Total Price"),
                    content: gettext("Enter the total amount for the line item. Unit price will be " +
                        "automatically calculated.")
                })
            ])
        ];
        const productPriceCells = [
            m("div.line-cell", [
                m("label", gettext("Qty")),
                renderNumberCell(store, line, line.quantity, "quantity", canEditPrice, true, 0),
                m.component(HelpPopover, {
                    title: gettext("Quantity"),
                    content: gettext("Enter the number of units of the product ordered.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Base Unit Price")),
                renderNumberCell(store, line, line.baseUnitPrice, "baseUnitPrice", false),
                m.component(HelpPopover, {
                    title: gettext("Base Unit Price"),
                    content: gettext("Enter the regular base price for a single unit of the product. " +
                        "If an existing product is selected, the price is already determined in product settings.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Discounted Unit Price")),
                renderNumberCell(store, line, line.unitPrice, "unitPrice", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Discounted Unit Price"),
                    content: gettext("Enter the total discounted price for a single product unit in the order. " +
                        "Discount percent, Total Discount Amount, and Line Total will be automatically calculated.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Discount Percent")),
                renderNumberCell(store, line, line.discountPercent, "discountPercent", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Discount Percent"),
                    content: gettext("Enter the discount percentage (%) for the line item. Discounted Unit " +
                        "Price, Total Discount Amount, and Line Total will be automatically.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Total Discount Amount")),
                renderNumberCell(store, line, line.discountAmount, "discountAmount", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Total Discount Amount"),
                    content: gettext("Enter the total discount amount for the line item. Discounted Unit Price, " +
                        "Discount percent, and Line Total will be automatically calculated.")
                })
            ]),
            m("div.line-cell", [
                m("label", gettext("Line Total")),
                renderNumberCell(store, line, line.total, "total", canEditPrice),
                m.component(HelpPopover, {
                    title: gettext("Line Total"),
                    content: gettext("Enter the total amount for the line item. Discounted Unit Price, Discount " +
                        "percent, and Total Discount Amount will be automatically calculated.")
                })
            ])
        ];
        if (line.type === "product" && line.product){
            editCell = m("div.line-cell.edit",
                m("button.btn.btn-sm.text-info", {
                    onclick: function(e) {
                        e.preventDefault();
                        window.open(line.product.url, "_blank");
                    }
                }, m("i.fa.fa-edit.fa-2x")));
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
                    }, m("i.fa.fa-trash.fa-2x")))
            ]),
            line.errors ? m("p.text-danger", line.errors) : null
        ]);
    }).compact().value();
}


var ProductQuickSelect = {
    view: function(ctrl, attrs) {
        const {store} = attrs;
        return m.component(Select2, {
            name: "product-quick-select",
            model: "shuup.product",
            searchMode: "sellable_mode_only",
            attrs: {
                placeholder: gettext("Search product by name, SKU, or barcode"),
                ajax: {
                    url: window.ShuupAdminConfig.browserUrls.select,
                    dataType: "json",
                    data: function (params) {
                        const data = {
                            model: "shuup.product",
                            searchMode: "sellable_mode_only",
                            search: params.term,
                        };
                        return data;
                    },
                    processResults(data) {
                        if (!data) {
                            return {results: []};
                        }
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
                if(product && product.length && !quickAdd.product.id) {
                    store.dispatch(addProduct(product[0]));
                }
            }
        });
    }
};

export function orderLinesView(store, isCreating) {
    const {lines, shop, quickAdd} = store.getState();
    let infoText = gettext("If your product prices vary based on customer, you might want to select customer first.");
    if(shop.selected.pricesIncludeTaxes) {
        infoText += " " + interpolate(gettext("All prices are in %s and include taxes."), [shop.selected.currency]);
    } else {
        infoText += " " + interpolate(gettext("All prices are in %s. Taxes not included"), [shop.selected.currency]);
    }
    return m("div", [
        m("p.alert.alert-info", [
            m("i.fa.fa-info-circle"),
            m("span", " " + infoText)
        ]),
        m("div.list-group", {id: "lines"}, renderOrderLines(store, shop.selected, lines)),
        m("hr"),
        m("div.row", [
            m("div.col-sm-8.col-md-6", {id: "quick-add"}, [
                m.component(ProductQuickSelect, {store: store}),
                m("button.btn.text-success", {
                    href: "#",
                    onclick: (e) => {
                        e.preventDefault();
                        window.BrowseAPI.openBrowseWindow({
                            kind: "product",
                            filter: {"shop": shop.id},
                            onSelect: (obj) => {
                                store.dispatch(addProduct(obj));
                            }
                        });
                    }
                }, m("i.fa.fa-search")),
                m.component(HelpPopover, {
                    title: gettext("Product Quick Adder"),
                    content: gettext("Search for products to add to the order by searching by name, SKU, or barcode or click the magnifying glass for more fine-grained filtering.")
                }, m("i.fa.fa-search")),
                m("p.mt-1", [
                    m("input", {
                        name: "auto-add",
                        type: "checkbox",
                        checked: quickAdd.autoAdd,
                        onchange: function() {
                            store.dispatch(setAutoAdd(this.checked));
                            store.dispatch(clearQuickAddProduct());
                        }
                    }),
                    m("span.quick-add-check-text", " " + gettext("Automatically add selected product"))
                ])
            ]),
            m("div.col-sm-4.col-md-6",
                m("button.btn.text-success.pull-right" + (isCreating ? ".disabled": ""), {
                    id: "add-line",
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
            )
        ])
    ]);
}
