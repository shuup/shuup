/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {setShippingMethod, setPaymentMethod, updateTotals} from "../actions";
import {selectBox, HelpPopover} from "./utils";

function renderMethod(store, mode, title, selectedMethod, choices, emptyChoice, helpText) {
    return [
        m("div.form-group.form-content", [
            m("label.control-label", title),
            m("div.form-input-group.d-flex", [
                selectBox(selectedMethod ? selectedMethod.id : 0, function () {
                    const newMethod = _.find(choices, {"id": parseInt(this.value)});
                    (mode === "shipping" ?
                        store.dispatch(setShippingMethod(newMethod)) : store.dispatch(setPaymentMethod(newMethod)));
                    store.dispatch(updateTotals(store.getState));
                }, [].concat({id: 0, name: emptyChoice}, choices || []), "id", "name", mode),
                m.component(HelpPopover, {
                    title: title,
                    content: helpText
                })
            ])
        ])
    ];
}

export function shipmentMethodSelectView(store) {
    const {methods} = store.getState();
    return renderMethod(
        store,
        "shipping",
        gettext("Shipping Method"),
        methods.shippingMethod,
        methods.shippingMethodChoices,
        gettext("No shipping method"),
        gettext("Select a shipping method for the order. These methods are defined in shipping settings.")
    );
}

export function paymentMethodSelectView(store) {
    const {methods} = store.getState();
    return renderMethod(
        store,
        "payment",
        gettext("Payment Method"),
        methods.paymentMethod,
        methods.paymentMethodChoices,
        gettext("No payment method"),
        gettext("Select a payment method for the order. These methods are defined in payment settings.")
    );
}
