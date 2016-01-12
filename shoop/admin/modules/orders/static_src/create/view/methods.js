/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {setShippingMethod, setPaymentMethod, updateTotals} from "../actions";
import {selectBox} from "./utils";

function renderMethod(store, mode, title, selectedMethod, choices, emptyChoice) {
    return [
        m("div.form-group", [
                m("label.control-label", title),
                selectBox(selectedMethod ? selectedMethod.id : 0, function () {
                    const newMethod = _.find(choices, {"id": parseInt(this.value)});
                    (mode === "shipping" ?
                        store.dispatch(setShippingMethod(newMethod)) : store.dispatch(setPaymentMethod(newMethod)));
                    store.dispatch(updateTotals(store.getState));
                }, [].concat({id: 0, name: emptyChoice}, choices || []))
            ]
        ),
        m("div", [
            (selectedMethod ? m("p.text-center", gettext("Price") + ": " + parseFloat(selectedMethod.price).toFixed(2)) : null)
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
        gettext("No shipping method")
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
        gettext("No payment method")
    );
}
