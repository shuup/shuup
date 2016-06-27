/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {setSelectedManufacturer} from "../actions";
import {selectBox} from "./utils";

export function manufacturerSelectView(store) {
    const {manufacturer} = store.getState();
    return m("div.form-group.required-field", [
        m("label.control-label", gettext("Manufacturer")),
        selectBox(manufacturer.selected, function(){
            store.dispatch(setSelectedManufacturer(this.value));
        }, manufacturer.all)
    ]);
}
