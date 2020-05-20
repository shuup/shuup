/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import _ from "lodash";
import m from "mithril";
import view from "./view";
import { persistStore } from "redux-persist";
import store from "./store";
import {
    setShopChoices,
    setCountries,
    setShop,
    setShippingMethodChoices,
    setPaymentMethodChoices,
    setCustomer,
    setAddressProperty,
    setShippingMethod,
    setPaymentMethod,
    setLines,
    setOrderId,
    updateTotals
} from "./actions";

var controller = null;

export function init(config = {}) {
    if (controller !== null) {
        return;
    }
    const persistor = persistStore(store, {
        keyPrefix: interpolate("order_creator_shop-%s-%s:", [config.shops[0].id, config.orderId])
    }, () => {
        var countryDefault = config.countryDefault;
        if (!countryDefault && config.countries.length > 0) {
            countryDefault = config.countries[0].id;
        }
        store.dispatch(setShopChoices(config.shops || []));
        store.dispatch(setShop(config.shops[0] || []));
        store.dispatch(setCountries(config.countries || []));
        store.dispatch(setAddressProperty("billing", "country", countryDefault));
        store.dispatch(setAddressProperty("shipping", "country", countryDefault));
        store.dispatch(setShippingMethodChoices(config.shippingMethods || []));
        store.dispatch(setPaymentMethodChoices(config.paymentMethods || []));
        const orderId = config.orderId;
        store.dispatch(setOrderId(orderId));
        const customerData = config.customerData;

        persistor.purge(["customerDetails", "quickAdd"]);
        const resetOrder = window.localStorage.getItem("resetSavedOrder") || "false";
        var savedOrder = { id: null };
        if (resetOrder === "true") {
            persistor.purge();
            window.localStorage.setItem("resetSavedOrder", "false");
        } else {
            const savedOrderStr = window.localStorage.getItem("reduxPersist:order");
            if (savedOrderStr) {
                savedOrder = JSON.parse(savedOrderStr);
            }
        }

        if (customerData) { // contact -> New Order
            persistor.purge();
            store.dispatch(setCustomer(customerData));
        }

        if (orderId) { // Edit mode
            if (!savedOrder.id || savedOrder.id !== orderId) {
                // Saved order id does not match with current order
                // Purge the wrong saved state and initialize from orderData
                persistor.purge();
                store.dispatch(setShop(config.orderData.shop));
                store.dispatch(setCustomer(config.orderData.customer));
                store.dispatch(setShippingMethod(config.orderData.shippingMethodId));
                store.dispatch(setPaymentMethod(config.orderData.paymentMethodId));
                store.dispatch(setLines(config.orderData.lines));
                store.dispatch(updateTotals(store.getState));
            }
        } else {  // New mode
            if (savedOrder.id) {
                // Purge the old saved state for existing order
                persistor.purge();
            }
        }
        controller = m.mount(document.getElementById("order-tool-container"), {
            view,
            controller: _.noop
        });
        store.subscribe(() => {
            m.redraw();
        });
    });
}

export function debugSaveState() {
    window.localStorage.setItem("_OrderCreatorState", JSON.stringify(store.getState()));
    console.log("Success! Saved.");  // eslint-disable-line no-console
}

export function debugLoadState() {
    const state = JSON.parse(window.localStorage.getItem("_OrderCreatorState"));
    store.dispatch({ "type": "_replaceState", "payload": state });
    console.log("Success! Loaded.");  // eslint-disable-line no-console
}
