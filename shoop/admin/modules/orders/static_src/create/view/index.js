/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import {shopSelectView} from "./shops";
import {orderLinesView} from "./lines";
import {customerSelectView} from "./customers";
import {manufacturerSelectView} from "./manufacturers";
import {shipmentMethodSelectView, paymentMethodSelectView} from "./methods";
import {confirmView} from "./confirm";
import {contentBlock} from "./utils";
import {beginFinalizingOrder, clearOrderSourceData, retrieveOrderSourceData} from "../actions";
import store from "../store";

function discardChangesButton() {
    return (
        m("div.container-fluid",
            m("button.btn.btn-gray.btn-inverse.pull-right", {
                onclick: () => {
                    window.localStorage.setItem("resetSavedOrder", "true");
                    window.location.reload();
                }
            }, m("i.fa.fa-undo"), " " + gettext("Discard Changes"))
        )
    );
}

function footer() {
    const {creating, source, total} = store.getState().order;
    const {selected} = store.getState().shop;

    return (
        m("div.order-footer",
            m("div.text", m(
                "small",
                gettext("Method rules, taxes and possible extra discounts are calculated after proceeding."))
            ),
            m("div.text", m("h2", m("small", gettext("Total") + ": "), total + " " + selected.currency)),
            m("div.proceed-button", [
                m("button.btn.btn-success.btn-block" + (creating ? ".disabled" : ""), {
                    disabled: creating,
                    onclick: () => {
                        if(!source) {
                            store.dispatch(retrieveOrderSourceData());
                        }
                    }
                }, m("i.fa.fa-check"), " " + gettext("Proceed"))
            ])
        )
    );
}

function salesOrderView() {
    const {creating} = store.getState().order;
    const {choices} = store.getState().shop;

    return [
        (choices.length > 1 ? contentBlock("i.fa.fa-building", gettext("Select Shop"), shopSelectView(store)) : null),
        contentBlock("i.fa.fa-user", gettext("Customer Details"), customerSelectView(store)),
        contentBlock("i.fa.fa-cubes", gettext("Order Contents"), orderLinesView(store, creating)),
        contentBlock("i.fa.fa-truck", gettext("Shipping Method"), shipmentMethodSelectView(store)),
        contentBlock("i.fa.fa-credit-card", gettext("Payment Method"), paymentMethodSelectView(store))
    ];
}

function purchaseOrderView() {
    const {creating} = store.getState().order;
    const {choices} = store.getState().shop;

    return [
        (choices.length > 1 ? contentBlock("i.fa.fa-building", gettext("Select Shop"), shopSelectView(store)) : null),
        contentBlock("i.fa.fa-user", gettext("Manufacturer Details"), manufacturerSelectView(store)),
        contentBlock("i.fa.fa-cubes", gettext("Order Contents"), orderLinesView(store, creating))
    ];
}

export default function view() {
    const {source, type} = store.getState().order;
    if (source) {
        return confirmView(store);
    } else {
        return [
            discardChangesButton(),
            m("div.container-fluid", type === "sales"? salesOrderView() : purchaseOrderView()),
            footer()
        ];
    }
}
