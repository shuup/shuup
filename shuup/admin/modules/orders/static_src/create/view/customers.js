/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {get} from "../api";
import {clearExistingCustomer, retrieveCustomerData, setAddressProperty,
    setAddressSavingOption, setShipToBillingAddress, setIsCompany, showCustomerModal, retrieveCustomerDetails} from "../actions";
import {ADDRESS_FIELDS, selectBox, contentBlock, infoRow, table, modal} from "./utils";
import BrowseAPI from "BrowseAPI";

function removeWarningBlocks(parentElement){
    var previousWarnings = parentElement.getElementsByClassName("duplicate-warning");

    while(previousWarnings[0]){
        previousWarnings[0].parentNode.removeChild(previousWarnings[0]);
    }
}

function buildWarningBlock(store, parentElement, fieldName, customerName, customerId) {
    var warningBlock = document.createElement("div");
    warningBlock.className = "duplicate-warning help-block";

    var warning = document.createElement("div");
    warning.innerHTML = interpolate(gettext("Customer with same %s already exists."), [fieldName]);
    warningBlock.appendChild(warning);

    var link = document.createElement("a");
    link.href = "#";
    link.onclick = function() {
        store.dispatch(retrieveCustomerData({id: customerId}));
        removeWarningBlocks(document);
    };
    link.innerHTML = interpolate(gettext("Click to select user %s."), [customerName]);
    warningBlock.appendChild(link);

    parentElement.appendChild(warningBlock);
}

function renderAddress(store, shop, customer, address, addressType) {
    return _(ADDRESS_FIELDS).map((field) => {
        const isRequired = (field.key === "tax_number" && customer.isCompany ? true : field.required);
        if (field.key === "country") {
            return m("div.form-group" + (isRequired ? " required-field" : ""), [
                m("label.control-label", field.label),
                selectBox(_.get(address, field.key, ""), function () {
                    store.dispatch(setAddressProperty(addressType, field.key, this.value));
                }, shop.countries, "id", "name", addressType + "-" + field.key)
            ]);
        }
        var onchange = function () {
            store.dispatch(setAddressProperty(addressType, field.key, this.value));
        };
        if (field.key === "tax_number" || field.key === "email"){
            onchange = function() {
                store.dispatch(setAddressProperty(addressType, field.key, this.value));
                get("customer_exists", {
                    "field": field.key, "value": this.value
                }).then((data) => {
                    removeWarningBlocks(this.parentElement);
                    if (data.id && data.id !== customer.id) {
                        buildWarningBlock(store, this.parentElement, field.label.toLowerCase(), data.name, data.id);
                    }
                });
            };
        }
        if (window.REGIONS) {
            const country = _.get(address, "country", "");
            let regionsData = window.REGIONS[country];
            if (regionsData) {
                if (field.key === "region_code") {
                    return m("div.form-group" + (isRequired ? " required-field" : ""), [
                        m("label.control-label", field.label),
                        selectBox(
                            _.get(address, field.key, ""), onchange, regionsData,
                            "code", "name", addressType + "-" + field.key, {code: "", name: "---------"})
                    ]);
                }
                if (field.key === "region") {
                    return null;
                }
            } else {
                if (field.key === "region_code") {
                    return null;
                }
            }
        } else {
            if (field.key === "region_code") {
                return null;
            }
        }

        return m("div.form-group" + (isRequired ? " required-field" : ""), [
            m("label.control-label", field.label),
            m("input.form-control", {
                type: "text",
                name: addressType + "-" + field.key,
                placeholder: field.label,
                required: isRequired,
                value: _.get(address, field.key, ""),
                onchange: onchange
            })
        ]);
    }).value();
}

function customerDetailView(customerInfo) {
    const groups = customerInfo.groups || [];
    const companies = customerInfo.companies || [];

    return (
        m("div.row",
            m("div.col-md-6",
                m("dl.dl-horizontal", [
                    infoRow(gettext("Full Name"), customerInfo.name),
                    infoRow(gettext("Phone"), customerInfo.phone_no),
                    infoRow(gettext("Email"), customerInfo.email),
                    infoRow(gettext("Tax Number"), customerInfo.tax_number)
                ])
            ),
            m("div.col-md-6",
                m("dl.dl-horizontal", [
                    infoRow(gettext("Groups"), groups.join(", ")),
                    infoRow(gettext("Companies"), companies.join(", ")),
                    infoRow(gettext("Merchant Notes"), customerInfo.merchant_notes)
                ])
            )
        )
    );
}

function orderSummaryView(orderSummary) {
    const columns = [
        {key: "year", label: gettext("Year")},
        {key: "total", label: gettext("Total Sales")}
    ];

    return m("div.table-responsive",
        table({
            tableClass: "table-condensed table-striped",
            columns,
            data: orderSummary
        })
    );
}

function recentOrderView(recentOrders) {
    const columns = [
        {key: "order_date", label: gettext("Date")},
        {key: "shipment_status", label: gettext("Shipment Status")},
        {key: "payment_status", label: gettext("Payment Status")},
        {key: "status", label: gettext("Order Status")},
        {key: "total", label: gettext("Total")}
    ];

    return m("div.table-responsive",
        table({
            tableClass: "table-condensed table-striped",
            columns,
            data: recentOrders
        })
    );
}

export function renderCustomerDetailModal(store) {
    const {customerDetails} = store.getState();

    const customerInfo = customerDetails.customerInfo || {};
    const orderSummary = customerDetails.orderSummary || [];
    const recentOrders = customerDetails.recentOrders || [];

    return modal({
        show: customerDetails.showCustomerModal,
        sizeClass: "modal-lg",
        close: () => store.dispatch(showCustomerModal(false)),
        title: m("h3.modal-title", customerInfo.name),
        body: [
            contentBlock("i.fa.fa-info-circle", gettext("Customer Information"), customerDetailView(customerInfo), "h3"),
            contentBlock("i.fa.fa-inbox", gettext("Order Summary"), orderSummaryView(orderSummary), "h3"),
            contentBlock("i.fa.fa-cubes", gettext("Recent Orders"), recentOrderView(recentOrders), "h3")
        ],
        footer: [
            m("button.btn.btn-default", {
                onclick: () => store.dispatch(showCustomerModal(false))
            }, gettext("Close"))
        ]
    });
}

export function customerSelectView(store) {
    const {customer, order, shop} = store.getState();
    return m("div.form-group", [
        ((!customer.id && !(order.id === null)) ? m("p.text-danger", gettext("Warning: No customer account is currently associated with this order.")) : null),
        (!customer.id ? m("p" + (!(order.id === null)? ".text-danger": ""), gettext("A new customer will be created based on billing address.")) : null),
        m("br"),
        m("div.clearfix", [
            m("label.control-label", gettext("Customer")),
            m("div.btn-group", [
                m("button.btn.btn-default" + (customer.id ? " active" : ""), {
                    id: "select-existing-customer",
                    onclick: () => {
                        BrowseAPI.openBrowseWindow({
                            kind: "contact",
                            clearable: true,
                            onSelect: (obj) => {
                                store.dispatch(retrieveCustomerData({id: obj.id}));
                            }
                        });
                    }
                    }, (customer.id ? [m("i.fa.fa-user"), " ", customer.name] : gettext("Select Existing Customer"))
                ),
                m("button.btn.btn-default" + (!customer.id ? " active" : ""), {
                    id: "new-customer",
                    onclick: () => {
                        store.dispatch(clearExistingCustomer());
                    }
                    }, [m("i.fa.fa-user"), " ", gettext("New Customer")]
                )
            ])
        ]),
        m("br"),
        m("div.clearfix " + (!customer.id? " hidden": ""), [
            m("label.control-label"),
            m("a[href='#customer-detail-view']", {
                onclick: (e) => {
                    e.preventDefault();
                    store.dispatch(retrieveCustomerDetails({id: customer.id})).then(() => {
                        store.dispatch(showCustomerModal(true));
                    });
                }
            }, gettext("View Details"))
        ]),
        m("hr"),
        m("label", [
            m("input", {
                name: "save-address",
                type: "checkbox",
                checked: customer.saveAddress,
                onchange: function() {
                    store.dispatch(setAddressSavingOption(this.checked));
                }
            }),
            " " + gettext("Save customer details while creating order")
        ]),
        m("label", [
            m("input", {
                name: "ship-to-billing-address",
                type: "checkbox",
                checked: customer.shipToBillingAddress,
                onchange: function() {
                    store.dispatch(setShipToBillingAddress(this.checked));
                }
            }),
            " " + gettext("Ship to billing address")
        ]),
        m("label", [
            m("input", {
                name: "order-for-company",
                type: "checkbox",
                checked: customer.isCompany,
                onchange: function() {
                    store.dispatch(setIsCompany(this.checked));
                }
            }),
            " " + gettext("Order for company")
        ]),
        m("br"),
        m("br"),
        m("hr"),
        m("div.row", [
            m("div.col-sm-6",
                m("fieldset", [
                    m("legend", gettext("Billing Address")),
                    m("br"),
                    renderAddress(store, shop, customer, customer.billingAddress, "billing")
                ])
            ),
            (!customer.shipToBillingAddress ?
                m("div.col-sm-6",
                    m("fieldset", [
                        m("legend", gettext("Shipping Address")),
                        m("br"),
                        renderAddress(store, shop, customer, customer.shippingAddress, "shipping")
                    ])
                ) : null)
        ])
    ]);
}
