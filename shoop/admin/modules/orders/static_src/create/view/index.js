/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import {shopSelectView, customerSelectView, methodSelectView, commentView} from "./meta";
import {orderLinesView} from "./lines";
import {beginCreatingOrder} from "../actions";
import store from "../store";

export default function view() {
    const isCreating = store.getState().order.creating;
    return m("div",
        m("div.row",
            m("div.col-md-4", [
                shopSelectView(store),
                customerSelectView(store),
                methodSelectView(store),
                commentView(store),
            ]),
            m("div.col-md-8", orderLinesView(store))
        ),
        m("hr"),
        m("div.row",
            m("div.col-md-4"),
            m("div.col-md-2.pull-right", [
                m("button.btn.btn-primary.btn-block" + (isCreating ? ".disabled" : ""), {
                    disabled: isCreating,
                    onclick: () => {
                        if(!isCreating) {
                            store.dispatch(beginCreatingOrder());
                        }
                    }
                }, m("i.fa.fa-check"), " " + gettext("Create Order"))
            ])
        )
    );
}
