/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { setShop, updateLines } from "../actions";
import { selectBox } from "./utils";

export function shopSelectView(store) {
    const { shop } = store.getState();
    return m("div.form-group", [
        m("label.control-label", gettext("Shop")),
        selectBox(shop.selected.id, function () {
            const newShop = _.find(shop.choices, { "id": parseInt(this.value) });
            store.dispatch(setShop(newShop));
            store.dispatch(updateLines());
        }, shop.choices)
    ]);
}
