/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function renderHeaders() {
    return  m("tr", [
        m("th", gettext("SKU")),
        m("th", gettext("Text")),
        m("th", gettext("Quantity")),
        m("th", gettext("Unit Price")),
        m("th", gettext("Discount amount")),
        m("th", gettext("Total (excluding taxes)")),
        m("th", gettext("Tax percent")),
        m("th", gettext("Total"))
    ]);
}

function renderLines(lines) {
    return _(lines).map((line) => {
        return m("tr", [
            m("td", line.sku),
            m("td", line.text),
            m("td", line.quantity),
            m("td", line.unitPrice),
            m("td", line.discountAmount),
            m("td", line.taxlessTotal),
            m("td", line.taxPercentage),
            m("td", line.taxfulTotal)
        ]);
    }).value();
}

function renderTotals(source) {
    return m("tr", [
        m("td", ""),
        m("td", ""),
        m("td", ""),
        m("td", ""),
        m("td", source.totalDiscountAmount),
        m("td", source.taxlessTotal),
        m("td", ""),
        m("td", source.taxfulTotal)
    ]);
}

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

export function confirmView(source) {
    return [
        m("div.table-responsive",
            m("table.table.table-striped", [
                m("thead", renderHeaders()),
                m("tbody", [
                    renderLines(source.orderLines),
                    renderTotals(source)
                ])
            ])
        ),
        m("div.row", [
            m("div.col-md-6", renderAddressBlock(gettext("Billing address"), source.billingAddress)),
            m("div.col-md-6", renderAddressBlock(gettext("Shipping address"), source.shippingAddress))
        ])
    ];
}
