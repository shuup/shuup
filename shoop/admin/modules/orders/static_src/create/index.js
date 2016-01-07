/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import _ from "lodash";
import m from "mithril";
import view from "./view";
import store from "./store";
import {setShopChoices, setCountries, setShop, setShippingMethodChoices, setPaymentMethodChoices} from "./actions";

var controller = null;

export function init(config = {}) {
    if (controller !== null) {
        return;
    }
    store.dispatch(setShopChoices(config.shops || []));
    store.dispatch(setCountries(config.countries || []));
    store.dispatch(setShop(config.shops[0] || []));
    store.dispatch(setShippingMethodChoices(config.shippingMethods || []));
    store.dispatch(setPaymentMethodChoices(config.paymentMethods || []));
    controller = m.mount(document.getElementById("order-tool-container"), {
        view,
        controller: _.noop
    });
    store.subscribe(() => {
        m.redraw();
    });
}

export function debugSaveState() {
    window.localStorage.setItem("_OrderCreatorState", JSON.stringify(store.getState()));
    console.log("Saved.");  // eslint-disable-line no-console
}

export function debugLoadState() {
    const state = JSON.parse(window.localStorage.getItem("_OrderCreatorState"));
    store.dispatch({"type": "_replaceState", "payload": state});
    console.log("Loaded.");  // eslint-disable-line no-console
}
