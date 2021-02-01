/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function renderHeaders() {
    return  m("tr", [
        m("th", gettext("SKU")),
        m("th", gettext("Text")),
        m("th.text-right", gettext("Quantity")),
        m("th.text-right", gettext("Unit Price")),
        m("th.text-right", gettext("Discounted Unit Price")),
        m("th.text-right", gettext("Discount amount")),
        m("th.text-right", gettext("Discount percent")),
        m("th.text-right", gettext("Total (excluding taxes)")),
        m("th.text-right", gettext("Tax percent")),
        m("th.text-right", gettext("Total"))
    ]);
}

function renderLines(lines) {
    return _(lines).map((line) => {
        return m("tr", [
            m("td", line.sku),
            m("td", line.text),
            m("td.text-right", line.quantity),
            m("td.text-right", line.unitPrice),
            m("td.text-right", line.discountedUnitPrice),
            m("td.text-right", line.discountAmount),
            m("td.text-right", line.discountPercent),
            m("td.text-right", line.taxlessTotal),
            m("td.text-right", line.taxPercentage),
            m("td.text-right", line.taxfulTotal)
        ]);
    }).value();
}

function renderTotals(source) {
    return m("tr", [
        m("td", ""),
        m("td", ""),
        m("td", ""),
        m("td", ""),
        m("td", ""),
        m("td.text-right", source.totalDiscountAmount),
        m("td", ""),
        m("td.text-right", source.taxlessTotal),
        m("td", ""),
        m("td.text-right", source.taxfulTotal)
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
    return m(".content",
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
    );
}
