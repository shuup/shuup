/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import {shopSelectView} from "./shops";
import {orderLinesView} from "./lines";
import {customerSelectView} from "./customers";
import {shipmentMethodSelectView, paymentMethodSelectView} from "./methods";
import {confirmView} from "./confirm";
import {contentBlock} from "./utils";
import {beginCreatingOrder, clearOrderSourceData, retrieveCustomerData, retrieveOrderSourceData} from "../actions";
import store from "../store";

export default function view() {
    const {creating, source, total} = store.getState().order;
    const {choices, selected} = store.getState().shop;
    if (source) {
        return m("div.container-fluid",
            confirmView(source),
            m("div", [
                m("button.btn.btn-danger.btn-lg" + (creating ? ".disabled" : ""), {
                    disabled: creating,
                    onclick: () => {
                        store.dispatch(clearOrderSourceData());
                    }
                }, m("i.fa.fa-close"), " " + gettext("Back")),
                m("button.btn.btn-success.btn-lg.pull-right" + (creating ? ".disabled" : ""), {
                    disabled: creating,
                    onclick: () => {
                        store.dispatch(beginCreatingOrder());
                    }
                }, m("i.fa.fa-check"), " " + gettext("Confirm"))
            ])
        );
    } else {
        return m("div.container-fluid",
            (choices.length > 1 ? contentBlock("i.fa.fa-building", gettext("Select Shop"), shopSelectView(store)) : null),
            contentBlock("i.fa.fa-cubes", gettext("Order Contents"), orderLinesView(store, creating)),
            contentBlock("i.fa.fa-user", gettext("Customer Details"), customerSelectView(store)),
            contentBlock("i.fa.fa-truck", gettext("Shipping Method"), shipmentMethodSelectView(store)),
            contentBlock("i.fa.fa-credit-card", gettext("Payment Method"), paymentMethodSelectView(store)),
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
}
