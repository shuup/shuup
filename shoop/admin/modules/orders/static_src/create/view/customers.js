/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {clearExistingCustomer, retrieveCustomerData, setAddressProperty,
    setAddressSavingOption, setShipToBillingAddress, setIsCompany} from "../actions";
import {ADDRESS_FIELDS, selectBox} from "./utils";
import BrowseAPI from "BrowseAPI";

function renderAddress(store, shop, customer, address, addressType) {
    return _(ADDRESS_FIELDS).map((field) => {
        const isRequired = (field.key === "tax_number" && customer.isCompany ? true : field.required);
        if (field.key === "country") {
            return m("div.form-group" + (isRequired ? " required-field" : ""), [
                m("label.control-label", field.label),
                selectBox(_.get(address, field.key, ""), function () {
                    store.dispatch(setAddressProperty(addressType, field.key, this.value));
                }, shop.countries)
            ]);
        }
        return m("div.form-group" + (isRequired ? " required-field" : ""), [
            m("label.control-label", field.label),
            m("input.form-control", {
                type: "text",
                placeholder: field.label,
                required: isRequired,
                value: _.get(address, field.key, ""),
                onchange: function () {
                    store.dispatch(setAddressProperty(addressType, field.key, this.value));
                }
            })
        ]);
    }).value();
}

export function customerSelectView(store) {
    const {customer, shop} = store.getState();
    return m("div.form-group", [
        (!customer.id ? m("p", gettext("A new customer will be created based on billing address.")) : null),
        m("br"),
        m("label.control-label", gettext("Customer")),
        m("div.btn-group", [
            m("button.btn.btn-default" + (customer.id ? " active" : ""), {
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
                onclick: () => {
                    store.dispatch(clearExistingCustomer());
                }
                }, [m("i.fa.fa-user"), " ", gettext("New Customer")]
            )
        ]),
        m("br"),
        m("hr"),
        m("label", [
            m("input", {
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
