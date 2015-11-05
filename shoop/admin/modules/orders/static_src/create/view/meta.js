/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {setCustomer, setShopId, setShippingMethodId, setComment} from "../actions";
import {selectBox} from "./utils";
import BrowseAPI from "BrowseAPI";

export function shopSelectView(store) {
    const {shop} = store.getState();
    return m("div.form-group", [
        m("label.control-label", "Shop"),
        selectBox(shop.id, function () {
            store.dispatch(setShopId(this.value));
        }, shop.choices)
    ]);
}

export function customerSelectView(store) {
    const {customer} = store.getState();
    return m("div.form-group", [
        m("label.control-label", "Customer"),
        m("button.btn.btn-default", {
            onclick: () => {
                BrowseAPI.openBrowseWindow({
                    kind: "contact",
                    onSelect: (obj) => {
                        store.dispatch(setCustomer(obj));
                    }
                });
            }
        }, (customer ? [m("i.fa.fa-user"), " ", customer.text] : "None selected"))
    ]);
}

export function methodSelectView(store) {
    const {methods} = store.getState();
    return m("div.form-group", [
        m("label.control-label", "Shipping Method"),
        selectBox(methods.shippingMethodId || 0, function () {
            store.dispatch(setShippingMethodId(this.value));
        }, [].concat({id: 0, name: "No shipping method"}, methods.shippingMethodChoices || []))
    ]);
}

export function commentView(store) {
    const {comment} = store.getState();
    return m("div.form-group", [
        m("label.control-label", "Order Notes"),
        m("textarea.form-control", {
            value: comment,
            onchange: function() { store.dispatch(setComment(this.value)); }
        })
    ]);
}
