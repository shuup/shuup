/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {table} from "./utils";
import {beginFinalizingOrder, clearOrderSourceData} from "../actions";

function renderAddress(address) {
    return _(address).map((line, index) => {
        if (index === 0) {
            return [
                m("strong", line),
                m("br")
            ];
        } else {
            return [
                line,
                m("br")
            ];
        }
    }).flatten().value();
}

function renderAddressBlock(title, address){
    return m("div",
        m("dl.dl-horizontal", [
            m("dt", title),
            m("dd", [
                m("address", renderAddress(address))
            ])
        ])
    );
}

function renderLinesTable(store) {
    const {type, source} = store.getState().order;
    var columns = [
        {key: "sku", label: gettext("SKU")},
        {key: "text", label: gettext("Text")},
        {key: "quantity", label: gettext("Quantity")},
        {key: "unitPrice", label: gettext("Unit Price")}
    ];
    if(type === 'sales'){
        columns.push({key: "discountAmount", label: gettext("Discount amount")});
    }
    columns = columns.concat([
        {key: "taxlessTotal", label: gettext("Total (excluding taxes)")},
        {key: "taxPercentage", label: gettext("Tax percent")},
        {key: "taxfulTotal", label: gettext("Total")}
    ]);
    const data = [
        ...source.orderLines, {
            discountAmount: source.totalDiscountAmount,
            taxlessTotal: source.taxlessTotal,
            taxfulTotal: source.taxfulTotal
        }
    ];

    return table({
        tableClass: "table-striped",
        columns,
        data
    })
}

export function confirmView(store) {
    const {type, creating, source} = store.getState().order;
    return m("div.container-fluid",
        m("div.table-responsive",
            renderLinesTable(store)
        ),
        type === 'sales'?
        m("div.row", [
            m("div.col-md-6", renderAddressBlock(gettext("Billing address"), source.billingAddress)),
            m("div.col-md-6", renderAddressBlock(gettext("Shipping address"), source.shippingAddress))
        ]): null,
        m("div", [
            m("button.btn.btn-danger.btn-lg" + (creating ? ".disabled" : ""), {
                disabled: creating,
                onclick: () => {
                    store.dispatch(clearOrderSourceData());
                }
            }, m("i.fa.fa-close"), " " + gettext("Back")),
            m("button.btn.btn-success.btn-lg.pull-right" + (creating ? ".disabled" : ""), {
                disabled: creating,
                onclick: () => {
                    store.dispatch(beginFinalizingOrder());
                }
            }, m("i.fa.fa-check"), " " + gettext("Confirm"))
        ])
    );
}
