/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

export default handleActions({
    setManufacturers: (state, {payload}) => {
        var updates = {};
        if(payload && payload.length > 0) {
            updates["all"] = payload;
            updates["selected"] = payload[0].id;
        }
        return _.assign({}, state, updates)
    },
    setSelectedManufacturer: (state, {payload}) => _.assign({}, state, {"selected": payload})
}, {
    all: [],
    selected: 0
});
