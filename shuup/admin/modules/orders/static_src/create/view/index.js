/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import { shopSelectView } from "./shops";
import { orderLinesView } from "./lines";
import { customerSelectView, renderCustomerDetailModal } from "./customers";
import { shipmentMethodSelectView, paymentMethodSelectView } from "./methods";
import { confirmView } from "./confirm";
import { contentBlock } from "./utils";
import { beginFinalizingOrder, clearOrderSourceData, retrieveOrderSourceData } from "../actions";
import store from "../store";
import ensureNumericValue from "../utils/numbers";

export default function view() {
    const {creating, source, total} = store.getState().order;
    const {choices, selected} = store.getState().shop;
    const {customerDetails} = store.getState();
    var viewObj;
    if (source) {
        viewObj = m("div.container-fluid",
            confirmView(source),
            m("div", [
                m("button.btn.btn-outline-danger.btn-lg" + (creating ? ".disabled" : ""), {
                    disabled: creating,
                    onclick: () => {
                        store.dispatch(clearOrderSourceData());
                    }
                }, m("i.fa.fa-close"), " " + gettext("Back")),
                m("button.btn.btn-success.btn-lg.pull-right" + (creating ? ".disabled" : ""), {
                    disabled: creating,
                    onclick: () => {
                        store.dispatch(beginFinalizingOrder());
                    }
                }, m("i.fa.fa-check"), " " + gettext("Confirm"))
            ])
        );
    } else {
        const choicesBlock = (
            choices.length > 1 ?
                contentBlock("i.fa.fa-building", gettext("Select Shop"), shopSelectView(store)) :
                null
        );
        viewObj = [
            m("div.container-fluid.text-right",
                m("button.btn.btn-inverse.mb-3", {
                    onclick: () => {
                        window.localStorage.setItem("resetSavedOrder", "true");
                        window.location.reload();
                    }
                }, m("i.fa.fa-undo"), " " + gettext("Discard Changes"))
            ),
            m("div.container-fluid",
                choicesBlock,
                contentBlock("i.fa.fa-user", gettext("Customer Details"), customerSelectView(store)),
                contentBlock("i.fa.fa-cubes", gettext("Order Contents"), orderLinesView(store, creating)),
                contentBlock("i.fa.fa-truck", gettext("Shipping Method"), shipmentMethodSelectView(store)),
                contentBlock("i.fa.fa-credit-card", gettext("Payment Method"), paymentMethodSelectView(store)),
                (customerDetails? renderCustomerDetailModal(store) : null),
                m("div.order-footer",
                    m("small.text.help-text",
                        gettext("Method rules, taxes and possible extra discounts are calculated after proceeding.")
                    ),
                    m(".total-container",
                        m("div.text.total",
                            m("h2",
                                m("small", gettext("Total") + ": "), ensureNumericValue(total) + " " + selected.currency)
                        ),
                        m("div.proceed-button",
                            m("button.btn.btn-success.btn-block" + (creating ? ".disabled" : ""), {
                                disabled: creating,
                                onclick: () => {
                                    if(!source) {
                                        store.dispatch(retrieveOrderSourceData());
                                    }
                                }
                            }, m("i.fa.fa-check"), " " + gettext("Proceed"))
                        )
                    )
                )
            )
        ];
    }
    return viewObj;
}
